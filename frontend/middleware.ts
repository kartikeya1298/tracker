import { NextRequest, NextResponse } from "next/server";

// Proxies /api/* to BACKEND_INTERNAL_URL (server-only, not NEXT_PUBLIC_) so the
// backend URL can be set via a runtime env var instead of a Docker build arg -
// needed on hosts like Render where a Blueprint service has no clean way to pass
// build-time ARGs. Middleware runs fresh on every request, unlike next.config.js's
// rewrites()/redirects()/headers(), which standalone builds compute once during
// `next build` and serialize into routes-manifest.json - a runtime env var set
// after that build has already happened has no effect on those.
export function middleware(request: NextRequest) {
  const backend = process.env.BACKEND_INTERNAL_URL;
  if (!backend) return NextResponse.next();
  const target = new URL(request.nextUrl.pathname + request.nextUrl.search, backend);
  return NextResponse.rewrite(target);
}

export const config = {
  matcher: "/api/:path*",
};
