import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../../api/client';

export default function ProfileSetup() {
  const [pseudonym, setPseudonym] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!pseudonym) {
      setError('Please provide a name or pseudonym.');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/patient/profile', { pseudonym });
      navigate('/patient/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to setup profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center text-teal-700 mb-6">Profile Setup</h2>
      <p className="text-sm text-gray-600 mb-6 text-center">
        To protect your privacy in the community spaces, please choose a pseudonym or display name. This can be your real name or a nickname.
      </p>

      {error && <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Display Name / Pseudonym</label>
          <input
            type="text"
            value={pseudonym}
            onChange={(e) => setPseudonym(e.target.value)}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-teal-500 focus:border-teal-500"
            placeholder="e.g. BraveFalcon"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Complete Setup'}
        </button>
      </form>
    </div>
  );
}
