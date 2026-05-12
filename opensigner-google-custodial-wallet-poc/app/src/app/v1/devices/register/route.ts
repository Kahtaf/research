import { z } from "zod";

import { DEFAULT_CHAIN_ID } from "@/lib/constants";
import { jsonResponse, optionsResponse } from "@/lib/cors";
import {
  authProvider,
  authenticatedOpenSignerUser,
  registerDeviceByAddress,
} from "@/lib/hot-storage";

export const runtime = "nodejs";

const schema = z.object({
  chainId: z.number().int().optional(),
  address: z.string().min(1),
  share: z.string().min(1),
  signerUuid: z.string().optional(),
});

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function POST(request: Request) {
  const userUuid = await authenticatedOpenSignerUser(request);
  if (!userUuid) {
    return jsonResponse(request, { error: "unauthorized" }, { status: 401 });
  }

  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) {
    return jsonResponse(request, { error: "invalid request" }, { status: 400 });
  }

  const response = await registerDeviceByAddress({
    userUuid,
    provider: authProvider(request),
    chainId: parsed.data.chainId || DEFAULT_CHAIN_ID,
    address: parsed.data.address,
    share: parsed.data.share,
    signerUuid: parsed.data.signerUuid,
  });

  return jsonResponse(request, response);
}
