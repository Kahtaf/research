import { z } from "zod";

import { DEFAULT_CHAIN_ID } from "@/lib/constants";
import {
  authProvider,
  authenticatedOpenSignerUser,
  createDevice,
} from "@/lib/hot-storage";
import { jsonResponse, optionsResponse } from "@/lib/cors";

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

  try {
    const response = await createDevice({
      userUuid,
      provider: authProvider(request),
      chainId: parsed.data.chainId || DEFAULT_CHAIN_ID,
      address: parsed.data.address,
      share: parsed.data.share,
      signerUuid: parsed.data.signerUuid,
    });
    return jsonResponse(request, response);
  } catch (error) {
    if (
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "ER_DUP_ENTRY"
    ) {
      return jsonResponse(request, { error: "account already exists" }, { status: 409 });
    }
    console.error("Failed to create hot storage device", {
      code: typeof error === "object" && error !== null && "code" in error ? error.code : null,
    });
    return jsonResponse(request, { error: "device creation failed" }, { status: 500 });
  }
}
