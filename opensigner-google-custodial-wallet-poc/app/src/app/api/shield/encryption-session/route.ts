import { jsonResponse } from "@/lib/cors";
import { requiredEnv } from "@/lib/env";
import { currentSession } from "@/lib/session";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const session = await currentSession();
  if (!session) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  const shieldUrl = requiredEnv("SHIELD_URL");
  const response = await fetch(`${shieldUrl}/project/encryption-session`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": requiredEnv("SHIELD_API_KEY"),
      "X-API-Secret": requiredEnv("SHIELD_API_SECRET"),
    },
    body: JSON.stringify({
      encryption_part: requiredEnv("OPENSIGNER_DEVELOPER_ENCRYPTION_PART"),
      user_id: session.opensignerUserUuid,
    }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    return jsonResponse(
      request,
      { error: "failed to create shield encryption session" },
      { status: response.status },
    );
  }

  return jsonResponse(request, { sessionId: body.session_id });
}
