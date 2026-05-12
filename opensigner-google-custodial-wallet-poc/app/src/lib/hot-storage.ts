import type { RowDataPacket } from "mysql2";
import { createCipheriv, createDecipheriv, randomBytes, randomUUID } from "node:crypto";

import { DEFAULT_CHAIN_ID } from "./constants";
import { exec, one, rows } from "./db";
import { bearerToken, verifyOpenSignerToken } from "./opensigner-jwt";

type AccountRow = RowDataPacket & {
  id: string;
  address: string;
  opensigner_user_uuid: string;
  chain_id: number;
  auth_provider: string;
  signer_id: string;
};

type DeviceRow = RowDataPacket & {
  id: string;
  encrypted_share: string;
  is_primary: number;
  signer_id: string;
  created_at: Date;
};

function shareEncryptionKey(): Buffer {
  const key = process.env.SHARE_ENCRYPTION_KEY || "";
  const buffer = Buffer.from(key, "hex");
  if (buffer.length !== 32) {
    throw new Error("SHARE_ENCRYPTION_KEY must be 64 hex chars");
  }
  return buffer;
}

function encryptShare(share: string): string {
  const nonce = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", shareEncryptionKey(), nonce);
  const ciphertext = Buffer.concat([cipher.update(share, "utf8"), cipher.final()]);
  return Buffer.concat([nonce, ciphertext, cipher.getAuthTag()]).toString("base64");
}

function decryptShare(payload: string): string {
  const raw = Buffer.from(payload, "base64");
  const nonce = raw.subarray(0, 12);
  const tag = raw.subarray(raw.length - 16);
  const ciphertext = raw.subarray(12, raw.length - 16);
  const decipher = createDecipheriv("aes-256-gcm", shareEncryptionKey(), nonce);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

export async function authenticatedOpenSignerUser(
  request: Request,
): Promise<string | null> {
  const token = bearerToken(request);
  if (!token) return null;
  return verifyOpenSignerToken(token);
}

export function authProvider(request: Request): string {
  return request.headers.get("x-auth-provider") || "authservice";
}

export async function listAccounts(userUuid: string, provider: string) {
  const accounts = await rows<AccountRow>(
    `SELECT * FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND auth_provider = ?
     ORDER BY created_at ASC`,
    [userUuid, provider],
  );

  return {
    object: "list",
    url: "/v2/accounts",
    data: accounts.map((account) => ({
      id: account.id,
      address: account.address,
      username: account.opensigner_user_uuid,
      chainId: account.chain_id,
      signerId: account.signer_id,
    })),
    start: 0,
    end: accounts.length ? accounts.length - 1 : 0,
    total: accounts.length,
  };
}

export async function createDevice(input: {
  userUuid: string;
  provider: string;
  chainId: number;
  address: string;
  share: string;
  signerUuid?: string;
}) {
  const signerId = input.signerUuid || randomUUID();
  const deviceId = randomUUID();
  const accountId = randomUUID();
  const encryptedShare = encryptShare(input.share);

  await exec("INSERT INTO hot_signers (id, created_at) VALUES (?, CURRENT_TIMESTAMP)", [
    signerId,
  ]);
  await exec(
    `INSERT INTO hot_devices
      (id, encrypted_share, is_primary, signer_id, created_at, updated_at)
     VALUES (?, ?, true, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
    [deviceId, encryptedShare, signerId],
  );
  await exec(
    `INSERT INTO hot_accounts
      (id, address, opensigner_user_uuid, chain_id, auth_provider, signer_id, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
    [
      accountId,
      input.address,
      input.userUuid,
      input.chainId || DEFAULT_CHAIN_ID,
      input.provider,
      signerId,
    ],
  );

  return {
    share: input.share,
    address: input.address,
    chainId: input.chainId || DEFAULT_CHAIN_ID,
    chainType: "EVM",
    deviceId,
    device: deviceId,
    account: accountId,
    ownerAddress: input.address,
    accountType: "Externally Owned Account",
    signer: `sig_${signerId}`,
  };
}

export async function recoverDevice(input: {
  userUuid: string;
  provider: string;
  accountId: string;
}) {
  const account = await one<AccountRow>(
    `SELECT * FROM hot_accounts
     WHERE id = ? AND opensigner_user_uuid = ? AND auth_provider = ?
     LIMIT 1`,
    [input.accountId, input.userUuid, input.provider],
  );
  if (!account) return null;

  const device = await one<DeviceRow>(
    `SELECT * FROM hot_devices
     WHERE signer_id = ? AND is_primary = true
     LIMIT 1`,
    [account.signer_id],
  );
  if (!device) return null;

  return {
    id: device.id,
    device: device.id,
    deviceId: device.id,
    deviceID: device.id,
    account: account.id,
    signerAddress: account.address,
    signer: `sig_${account.signer_id}`,
    share: decryptShare(device.encrypted_share),
    isPrimary: Boolean(device.is_primary),
    user: account.opensigner_user_uuid,
    chainType: "EVM",
  };
}

export async function getDevice(input: {
  userUuid: string;
  provider: string;
  deviceId: string;
}) {
  const device = await one<DeviceRow & { address: string }>(
    `SELECT d.*, a.address
     FROM hot_devices d
     INNER JOIN hot_accounts a ON a.signer_id = d.signer_id
     WHERE d.id = ? AND a.opensigner_user_uuid = ? AND a.auth_provider = ?
     LIMIT 1`,
    [input.deviceId, input.userUuid, input.provider],
  );
  if (!device) return null;

  return {
    id: device.id,
    object: "device",
    createdAt: Math.floor(new Date(device.created_at).getTime() / 1000),
    address: device.address,
    share: decryptShare(device.encrypted_share),
    isPrimary: Boolean(device.is_primary),
    signer: `sig_${device.signer_id}`,
    chainType: "EVM",
  };
}

export async function exportedDevice(input: {
  userUuid: string;
  provider: string;
  address: string;
}): Promise<boolean> {
  const account = await one<AccountRow>(
    `SELECT id FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND auth_provider = ? AND address = ?
     LIMIT 1`,
    [input.userUuid, input.provider, input.address],
  );
  return Boolean(account);
}

export async function registerDevice(input: {
  userUuid: string;
  provider: string;
  accountId: string;
  share: string;
}) {
  const account = await one<AccountRow>(
    `SELECT * FROM hot_accounts
     WHERE id = ? AND opensigner_user_uuid = ? AND auth_provider = ?
     LIMIT 1`,
    [input.accountId, input.userUuid, input.provider],
  );
  if (!account) return null;

  await exec(
    `UPDATE hot_devices
     SET encrypted_share = ?, updated_at = CURRENT_TIMESTAMP
     WHERE signer_id = ? AND is_primary = true`,
    [encryptShare(input.share), account.signer_id],
  );

  return recoverDevice(input);
}

export async function registerDeviceByAddress(input: {
  userUuid: string;
  provider: string;
  chainId: number;
  address: string;
  share: string;
  signerUuid?: string;
}) {
  const account = await one<AccountRow>(
    `SELECT * FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND auth_provider = ? AND address = ?
     LIMIT 1`,
    [input.userUuid, input.provider, input.address],
  );

  if (!account) {
    return createDevice(input);
  }

  await exec(
    `UPDATE hot_devices
     SET encrypted_share = ?, updated_at = CURRENT_TIMESTAMP
     WHERE signer_id = ? AND is_primary = true`,
    [encryptShare(input.share), account.signer_id],
  );

  return {
    share: input.share,
    address: account.address,
    chainId: account.chain_id,
    chainType: "EVM",
    device: (await recoverDevice({
      userUuid: input.userUuid,
      provider: input.provider,
      accountId: account.id,
    }))?.id,
    account: account.id,
    ownerAddress: account.address,
    accountType: "Externally Owned Account",
    signer: `sig_${account.signer_id}`,
  };
}

export async function initDevice(input: {
  userUuid: string;
  provider: string;
  chainId: number;
}) {
  const account = await one<AccountRow>(
    `SELECT * FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND chain_id = ? AND auth_provider = ?
     LIMIT 1`,
    [input.userUuid, input.chainId || DEFAULT_CHAIN_ID, input.provider],
  );

  if (!account) {
    return {
      nextAction: "REGISTER",
      player: input.userUuid,
      embedded: { chainId: input.chainId || DEFAULT_CHAIN_ID },
    };
  }

  const recovered = await recoverDevice({
    userUuid: input.userUuid,
    provider: input.provider,
    accountId: account.id,
  });

  return {
    nextAction: "RECOVER",
    player: input.userUuid,
    embedded: {
      chainId: account.chain_id,
      address: account.address,
      device: recovered?.id,
      deviceId: recovered?.id,
      deviceID: recovered?.id,
      share: recovered?.share,
    },
  };
}
