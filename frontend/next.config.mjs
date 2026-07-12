/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // BACKEND_INTERNAL_URL (server-only, not NEXT_PUBLIC_) is read at request time,
  // not baked in at build time - lets the frontend image be built once and pointed
  // at any backend URL via a runtime env var (needed on hosts like Render where a
  // Docker build-time ARG isn't available for services declared in a Blueprint).
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL;
    if (!backend) return [];
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
