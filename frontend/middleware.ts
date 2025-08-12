import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Define protected routes that require authentication
const isProtectedRoute = createRouteMatcher([
  '/',
  '/team-management',
  '/query', 
  '/memory',
  '/integrations',
  '/settings',
  '/reports',
  '/analytics',
  '/help',
  '/trust',
  '/team'
])

export default clerkMiddleware((auth, req) => {
  const { pathname } = req.nextUrl

  // Allow public access to auth pages, debug pages, etc.
  const publicRoutes = [
    '/signin',
    '/signup',
    '/auth',
    '/working', 
    '/simple',
    '/debug',
    '/test',
    '/signout'
  ]

  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route))
  
  // If it's a protected route and user is not authenticated, redirect to signin
  if (isProtectedRoute(req) && !isPublicRoute) {
    auth().protect()
  }
})

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}