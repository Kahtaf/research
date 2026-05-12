import type { RowDataPacket } from "mysql2";

import { jsonResponse, optionsResponse } from "@/lib/cors";
import { one } from "@/lib/db";
import { authProvider, authenticatedOpenSignerUser } from "@/lib/hot-storage";

export const runtime = "nodejs";

type AccountRow = RowDataPacket & { signer_id: string };

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function GET(request: Request) {
  const userUuid = await authenticatedOpenSignerUser(request);
  if (!userUuid) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  const address = new URL(request.url).searchParams.get("address");
  if (!address) {
    return jsonResponse(request, { error: "address is required" }, { status: 400 });
  }

  const account = await one<AccountRow>(
    `SELECT signer_id FROM hot_accounts
     WHERE opensigner_user_uuid = ? AND auth_provider = ? AND address = ?
     LIMIT 1`,
    [userUuid, authProvider(request), address],
  );

  if (!account) {
    return jsonResponse(request, { error: "not found" }, { status: 404 });
  }

  return jsonResponse(request, { id: `sig_${account.signer_id}` });
}
