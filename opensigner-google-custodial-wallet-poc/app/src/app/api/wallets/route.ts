import { z } from "zod";

import { jsonResponse } from "@/lib/cors";
import { currentSession } from "@/lib/session";
import { upsertWallet } from "@/lib/repos";

export const runtime = "nodejs";

const schema = z.object({
  address: z.string().min(1),
  opensignerAccountUuid: z.string().nullable().optional(),
});

export async function POST(request: Request) {
  const session = await currentSession();
  if (!session) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) {
    return jsonResponse(request, { error: "invalid request" }, { status: 400 });
  }

  const wallet = await upsertWallet({
    internalUserId: session.userId,
    opensignerUserUuid: session.opensignerUserUuid,
    opensignerAccountUuid: parsed.data.opensignerAccountUuid || null,
    walletAddress: parsed.data.address,
  });

  return jsonResponse(request, {
    id: wallet.id,
    address: wallet.wallet_address,
    opensignerAccountUuid: wallet.opensigner_account_uuid,
    custodyModel: wallet.custody_model,
    recoveryMethod: wallet.recovery_method,
  });
}
