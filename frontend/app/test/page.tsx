export default function TestPage() {
  return (
    <div className="min-h-screen bg-blue-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-900">Test Page Works!</h1>
        <p className="mt-4 text-blue-600">This confirms Next.js routing is working</p>
        <a href="/auth/sign-in" className="mt-4 inline-block text-blue-600 underline">
          Go to Sign In
        </a>
      </div>
    </div>
  )
}