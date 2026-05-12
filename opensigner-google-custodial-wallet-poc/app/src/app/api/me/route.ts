import { NextResponse } from "next/server";

import { CUSTODY_MODEL, RECOVERY_METHOD } from "@/lib/constants";
import { currentWallet } from "@/lib/repos";
import { currentSession } from "@/lib/session";
import { createOpenSignerToken } from "@/lib/opensigner-jwt";

export const runtime = "nodejs";

export async function GET() {
  const session = await currentSession();
  if (!session) {
    return NextResponse.json({
      authenticated: false,
      signInUrl: "/api/auth/google",
    });
  }

  const wallet = await currentWallet(session.userId);
  const openSignerToken = await createOpenSignerToken(session.opensignerUserUuid);

  return NextResponse.json({
    authenticated: true,
    email: session.email,
    userId: session.userId,
    opensignerUserUuid: session.opensignerUserUuid,
    openSignerToken,
    wallet: wallet
      ? {
          id: wallet.id,
          address: wallet.wallet_address,
          opensignerAccountUuid: wallet.opensigner_account_uuid,
          custodyModel: wallet.custody_model,
          recoveryMethod: wallet.recovery_method,
        }
      : null,
    walletDefaults: {
      custodyModel: CUSTODY_MODEL,
      recoveryMethod: RECOVERY_METHOD,
    },
    config: {
      iframeUrl: process.env.NEXT_PUBLIC_OPENSIGNER_IFRAME_URL || "",
      hotStorageUrl: process.env.NEXT_PUBLIC_HOT_STORAGE_URL || "",
      shieldUrl: process.env.NEXT_PUBLIC_SHIELD_URL || "",
      shieldApiKey: process.env.NEXT_PUBLIC_SHIELD_API_KEY || "",
      chainId: Number(process.env.NEXT_PUBLIC_CHAIN_ID || 1),
    },
  });
}
