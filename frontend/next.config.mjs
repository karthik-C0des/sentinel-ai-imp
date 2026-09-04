/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/fraud/:path*',
        destination: 'http://54.84.190.5:8000/:path*', // Proxy to EC2 Fraud API
      },
      {
        source: '/api/aml/:path*',
        destination: 'http://54.84.190.5:8001/:path*', // Proxy to EC2 AML API
      },
    ];
  },
};

export default nextConfig;
