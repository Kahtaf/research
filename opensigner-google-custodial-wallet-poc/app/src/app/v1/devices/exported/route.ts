import { z } from "zod";
import { corsHeaders, jsonResponse, optionsResponse } from "@/lib/cors";
import {
  authProvider,
  authenticatedOpenSignerUser,
  exportedDevice,
} from "@/lib/hot-storage";

export const runtime = "nodejs";

const schema = z.object({ address: z.string().min(1) });

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

  const exported = await exportedDevice({
    userUuid,
    provider: authProvider(request),
    address: parsed.data.address,
  });
  if (!exported) {
    return jsonResponse(request, { error: "not found" }, { status: 404 });
  }

  return new Response(null, {
    status: 201,
    headers: corsHeaders(request),
  });
}
