import { getAddress, hashMessage, id, verifyMessage } from "ethers";
import { z } from "zod";

import { DEMO_MESSAGE } from "@/lib/constants";
import { jsonResponse } from "@/lib/cors";
import { currentWallet, insertSigningAudit } from "@/lib/repos";
import { currentSession } from "@/lib/session";

export const runtime = "nodejs";

const schema = z.object({
  walletId: z.string().min(1),
  walletAddress: z.string().min(1),
  message: z.literal(DEMO_MESSAGE),
  signature: z.string().min(1),
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

  const wallet = await currentWallet(session.userId);
  if (!wallet || wallet.id !== parsed.data.walletId) {
    return jsonResponse(request, { error: "wallet not found" }, { status: 404 });
  }

  let verified = false;
  try {
    const recovered = verifyMessage(parsed.data.message, parsed.data.signature);
    verified =
      getAddress(recovered) === getAddress(parsed.data.walletAddress) &&
      getAddress(wallet.wallet_address) === getAddress(parsed.data.walletAddress);
  } catch {
    verified = false;
  }

  await insertSigningAudit({
    internalUserId: session.userId,
    walletId: wallet.id,
    walletAddress: parsed.data.walletAddress,
    messageHash: hashMessage(parsed.data.message),
    signatureHash: id(parsed.data.signature),
    verificationResult: verified,
  });

  return jsonResponse(request, { verified });
}
