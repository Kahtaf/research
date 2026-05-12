import type { RowDataPacket } from "mysql2";
import { randomUUID } from "node:crypto";

import { CUSTODY_MODEL, RECOVERY_METHOD } from "./constants";
import { exec, one } from "./db";

export type UserRow = RowDataPacket & {
  id: string;
  google_sub: string;
  google_email: string;
  opensigner_user_uuid: string;
};

export type WalletRow = RowDataPacket & {
  id: string;
  internal_user_id: string;
  opensigner_user_uuid: string;
  opensigner_account_uuid: string | null;
  wallet_address: string;
  custody_model: string;
  recovery_method: string;
};

export async function findOrCreateUser(
  googleSub: string,
  email: string,
): Promise<UserRow> {
  const existing = await one<UserRow>(
    "SELECT * FROM users WHERE google_sub = ? LIMIT 1",
    [googleSub],
  );

  if (existing) {
    await exec(
      "UPDATE users SET google_email = ?, last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
      [email, existing.id],
    );
    return { ...existing, google_email: email };
  }

  const id = randomUUID();
  const opensignerUserUuid = randomUUID();
  await exec(
    `INSERT INTO users
      (id, google_sub, google_email, opensigner_user_uuid, created_at, last_login_at)
     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
    [id, googleSub, email, opensignerUserUuid],
  );

  const created = await one<UserRow>("SELECT * FROM users WHERE id = ? LIMIT 1", [
    id,
  ]);
  if (!created) throw new Error("created user not found");
  return created;
}

export async function currentWallet(userId: string): Promise<WalletRow | null> {
  return one<WalletRow>(
    "SELECT * FROM wallets WHERE internal_user_id = ? ORDER BY created_at DESC LIMIT 1",
    [userId],
  );
}

export async function upsertWallet(input: {
  internalUserId: string;
  opensignerUserUuid: string;
  opensignerAccountUuid: string | null;
  walletAddress: string;
}): Promise<WalletRow> {
  const id = randomUUID();
  await exec(
    `INSERT INTO wallets
      (id, internal_user_id, opensigner_user_uuid, opensigner_account_uuid,
       wallet_address, custody_model, recovery_method, created_at, last_used_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
     ON DUPLICATE KEY UPDATE
       opensigner_account_uuid = VALUES(opensigner_account_uuid),
       wallet_address = VALUES(wallet_address),
       custody_model = VALUES(custody_model),
       recovery_method = VALUES(recovery_method),
       last_used_at = CURRENT_TIMESTAMP`,
    [
      id,
      input.internalUserId,
      input.opensignerUserUuid,
      input.opensignerAccountUuid,
      input.walletAddress,
      CUSTODY_MODEL,
      RECOVERY_METHOD,
    ],
  );

  const wallet = await currentWallet(input.internalUserId);
  if (!wallet) throw new Error("wallet upsert failed");
  return wallet;
}

export async function insertSigningAudit(input: {
  internalUserId: string;
  walletId: string;
  walletAddress: string;
  messageHash: string;
  signatureHash: string;
  verificationResult: boolean;
}): Promise<void> {
  await exec(
    `INSERT INTO signing_audit_logs
      (id, internal_user_id, wallet_id, wallet_address, message_hash,
       signature_hash, verification_result, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`,
    [
      randomUUID(),
      input.internalUserId,
      input.walletId,
      input.walletAddress,
      input.messageHash,
      input.signatureHash,
      input.verificationResult,
    ],
  );
}
