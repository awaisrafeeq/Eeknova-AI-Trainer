/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use stable webpack instead of turbopack
  webpack: (config, { dev, isServer }) => {
    return config;
  },
  // Add turbopack config to silence the warning
  turbopack: {},
}

module.exports = nextConfig
