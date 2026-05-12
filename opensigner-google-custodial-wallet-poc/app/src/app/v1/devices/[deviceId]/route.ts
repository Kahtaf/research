import { jsonResponse, optionsResponse } from "@/lib/cors";
import {
  authProvider,
  authenticatedOpenSignerUser,
  getDevice,
  recoverDevice,
} from "@/lib/hot-storage";
import { one } from "@/lib/db";
import type { RowDataPacket } from "mysql2";

export const runtime = "nodejs";

type AccountRow = RowDataPacket & { id: string };

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function GET(
  request: Request,
  context: { params: Promise<{ deviceId: string }> },
) {
  const userUuid = await authenticatedOpenSignerUser(request);
  if (!userUuid) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  const { deviceId } = await context.params;
  if (deviceId !== "primary") {
    const device = await getDevice({
      userUuid,
      provider: authProvider(request),
      deviceId,
    });
    if (!device) {
      return jsonResponse(request, { error: "not found" }, { status: 404 });
    }
    return jsonResponse(request, device);
  }

  const account = await one<AccountRow>(
    `SELECT id FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND auth_provider = ?
     ORDER BY created_at ASC LIMIT 1`,
    [userUuid, authProvider(request)],
  );
  if (!account) {
    return jsonResponse(request, { error: "not found" }, { status: 404 });
  }

  const recovered = await recoverDevice({
    userUuid,
    provider: authProvider(request),
    accountId: account.id,
  });
  if (!recovered) {
    return jsonResponse(request, { error: "not found" }, { status: 404 });
  }

  return jsonResponse(request, {
    id: recovered.id,
    object: "device",
    createdAt: Math.floor(Date.now() / 1000),
    address: recovered.signerAddress,
    share: recovered.share,
    isPrimary: recovered.isPrimary,
    chainType: "EVM",
  });
}
