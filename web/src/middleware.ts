import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ALLOWED_PREFIXES = ["/_next", "/favicon.ico"];

export function middleware(request: NextRequest) {
  if (process.env.LANDING_ONLY !== "true") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;

  if (pathname === "/") {
    return NextResponse.next();
  }

  if (ALLOWED_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  return NextResponse.redirect(new URL("/", request.url));
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
