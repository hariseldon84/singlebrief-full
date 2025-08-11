export default function SimplePage() {
  return (
    <div className="min-h-screen bg-green-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-green-900">Simple Page Works!</h1>
        <p className="mt-4 text-green-600">No authentication, just basic Next.js</p>
        <a href="/signin" className="mt-4 inline-block bg-green-600 text-white px-4 py-2 rounded">
          Go to Sign In
        </a>
      </div>
    </div>
  )
}