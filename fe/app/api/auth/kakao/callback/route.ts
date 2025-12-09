import { NextRequest, NextResponse } from "next/server";

const KAKAO_CLIENT_ID = process.env.KAKAO_CLIENT_ID;
const KAKAO_REDIRECT_URI = "http://localhost:3000/api/auth/kakao/callback";

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");

  if (!code) {
    return NextResponse.json({ error: "No code provided" }, { status: 400 });
  }

  // STEP 1: code로 토큰 요청
  const tokenResponse = await fetch("https://kauth.kakao.com/oauth/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: KAKAO_CLIENT_ID!,
      redirect_uri: KAKAO_REDIRECT_URI,
      code,
    }),
  });

  const tokenData = await tokenResponse.json();

  if (tokenData.error) {
    return NextResponse.json(tokenData, { status: 400 });
  }

  const accessToken = tokenData.access_token;

  // STEP 2: 사용자 정보 조회
  const userResponse = await fetch("https://kapi.kakao.com/v2/user/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    },
  });

  const userData = await userResponse.json();

  // 이후 JWT 만들기 or DB 저장 처리

  return NextResponse.json({
    message: "Kakao login success",
    user: userData,
  });
}