import { authProvider, authenticatedOpenSignerUser, listAccounts } from "@/lib/hot-storage";
import { jsonResponse, optionsResponse } from "@/lib/cors";

export const runtime = "nodejs";

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function GET(request: Request) {
  const userUuid = await authenticatedOpenSignerUser(request);
  if (!userUuid) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  return jsonResponse(request, await listAccounts(userUuid, authProvider(request)));
}
