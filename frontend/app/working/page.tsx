export default function WorkingPage() {
  return (
    <div className="min-h-screen bg-blue-50 flex items-center justify-center">
      <div className="text-center bg-white p-8 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-blue-900 mb-4">✅ Application Working!</h1>
        <p className="text-blue-600 mb-6">The frontend is running correctly</p>
        <div className="space-y-4">
          <a href="/signin" className="block bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">
            Test Sign In Page
          </a>
          <a href="/debug" className="block bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700">
            Debug Auth State
          </a>
          <a href="/simple" className="block bg-purple-600 text-white px-6 py-3 rounded hover:bg-purple-700">
            Simple Test Page
          </a>
        </div>
      </div>
    </div>
  )
}