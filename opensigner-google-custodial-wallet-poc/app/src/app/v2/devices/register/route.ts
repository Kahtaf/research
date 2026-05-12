import { z } from "zod";

import {
  authProvider,
  authenticatedOpenSignerUser,
  registerDevice,
} from "@/lib/hot-storage";
import { jsonResponse, optionsResponse } from "@/lib/cors";

export const runtime = "nodejs";

const schema = z.object({
  account: z.string().min(1),
  share: z.string().min(1),
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

  const response = await registerDevice({
    userUuid,
    provider: authProvider(request),
    accountId: parsed.data.account,
    share: parsed.data.share,
  });

  if (!response) {
    return jsonResponse(request, { error: "not found" }, { status: 404 });
  }

  return jsonResponse(request, response);
}
