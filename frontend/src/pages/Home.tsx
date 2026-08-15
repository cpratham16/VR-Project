import { useEffect, useState } from 'react';
import { checkHealth } from '../api/client';

export default function Home() {
  const [health, setHealth] = useState<string>('checking...');

  useEffect(() => {
    checkHealth()
      .then((data) => setHealth(data.status))
      .catch(() => setHealth('API offline'));
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Welcome</h2>
      <p>
        API Status: <span className="font-bold">{health}</span>
      </p>
      
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <a href="/patient" className="p-4 bg-teal-50 text-teal-800 rounded-lg text-center hover:bg-teal-100 transition">
          Patient Portal
        </a>
        <a href="/doctor" className="p-4 bg-blue-50 text-blue-800 rounded-lg text-center hover:bg-blue-100 transition">
          Doctor Portal
        </a>
        <a href="/admin" className="p-4 bg-purple-50 text-purple-800 rounded-lg text-center hover:bg-purple-100 transition">
          Admin Portal
        </a>
      </div>
    </div>
  );
}
