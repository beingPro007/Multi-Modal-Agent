// /pages/api/token.ts or /app/api/token/route.ts
import { NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";

// Edge-compatible function
export async function GET(req: Request) {
  const url = new URL(req.url);
  const room = url.searchParams.get("room");

  if (!room) {
    return NextResponse.json({ error: "Missing room" }, { status: 400 });
  }

  const apiKey = process.env.LIVEKIT_API_KEY!;
  const apiSecret = process.env.LIVEKIT_API_SECRET!;
  const identity = `user_${Math.floor(Math.random() * 100000)}`;

  const at = new AccessToken(apiKey, apiSecret, { identity });
  at.addGrant({ roomJoin: true, room });

  return NextResponse.json({ token: await at.toJwt() });
}
