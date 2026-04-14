/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/api/inference/:path*", destination: "http://localhost:8000/:path*" },
      { source: "/api/drift/:path*", destination: "http://localhost:8001/:path*" },
    ];
  },
};

export default nextConfig;
