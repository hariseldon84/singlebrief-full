
export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-6">SingleBrief</h1>
      <p className="text-xl mb-8">Answers from everyone. Delivered by one.</p>
      <div className="p-6 bg-white rounded-lg shadow-lg">
        <h2 className="text-2xl font-semibold mb-4">Welcome to the development environment</h2>
        <p className="mb-4">The application is now running successfully.</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Frontend: Running on port 3000</li>
          <li>Backend API: Running on port 8000 (after fixes)</li>
          <li>Database: PostgreSQL on port 5432</li>
          <li>Cache: Redis on port 6379</li>
          <li>Task Monitor: Celery Flower on port 5555</li>
        </ul>
      </div>
    </div>
  );
}
