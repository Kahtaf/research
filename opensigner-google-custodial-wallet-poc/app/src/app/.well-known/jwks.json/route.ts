import { NextResponse } from "next/server";

import { publicJwks } from "@/lib/opensigner-jwt";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json(await publicJwks());
}
