/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  // Set the source directory to use src/app instead of app
  distDir: 'build',
  reactStrictMode: true,
}

module.exports = nextConfig