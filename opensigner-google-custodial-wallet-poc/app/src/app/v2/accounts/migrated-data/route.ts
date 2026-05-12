import { jsonResponse, optionsResponse } from "@/lib/cors";

export const runtime = "nodejs";

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function GET(request: Request) {
  return jsonResponse(request, { error: "not found" }, { status: 404 });
}
