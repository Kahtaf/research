import { jsonResponse } from "@/lib/cors";
import { resetWalletForUser } from "@/lib/repos";
import { currentSession } from "@/lib/session";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const session = await currentSession();
  if (!session) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  await resetWalletForUser({
    internalUserId: session.userId,
    opensignerUserUuid: session.opensignerUserUuid,
  });

  return jsonResponse(request, { reset: true });
}
