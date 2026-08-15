import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../../api/client';

export default function ConsentScreen() {
  const [agreedData, setAgreedData] = useState(false);
  const [agreedAI, setAgreedAI] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  
  const CURRENT_CONSENT_VERSION = "v1.0";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!agreedData || !agreedAI) {
      setError('You must agree to all terms before proceeding.');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/patient/consent', {
        consent_version: CURRENT_CONSENT_VERSION,
        agreed_to_data_usage: agreedData,
        agreed_to_ai_processing: agreedAI
      });
      // Redirect to profile setup
      navigate('/patient/onboarding/profile');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit consent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-teal-700 mb-6">Informed Consent</h2>
      
      <div className="prose prose-sm text-gray-700 mb-6 max-h-96 overflow-y-auto p-4 border border-gray-200 rounded">
        <h3 className="text-lg font-semibold mb-2">Welcome to the VR Mental Health Platform</h3>
        <p>Before you begin, please read and understand how your data will be captured, processed, and stored.</p>
        
        <h4 className="font-semibold mt-4">1. Data Usage & Confidentiality</h4>
        <p>Your clinical data, journal entries, and screening scores will be kept strictly confidential. Only your assigned medical professional (doctor/counselor) will have access to any identifiable information you provide. Aggregated, anonymized statistics will be shared with the institutional panels for resource planning, but no single-patient-identifiable record will be shared.</p>
        
        <h4 className="font-semibold mt-4">2. AI Processing</h4>
        <p>Our platform uses advanced Artificial Intelligence (AI) to power the supportive chat companion and detect crisis signals. The companion is <strong>not a therapist</strong> and cannot diagnose you. By using this service, you consent to have your textual input (messages and journals) processed by an AI to provide support and risk assessment.</p>
        
        <h4 className="font-semibold mt-4">3. Right to Withdraw</h4>
        <p>You may discontinue use of this service or request your data be deleted at any point by contacting your campus wellness office.</p>
      </div>

      {error && <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="flex items-start space-x-3">
          <input 
            type="checkbox" 
            checked={agreedData} 
            onChange={(e) => setAgreedData(e.target.checked)}
            className="mt-1 h-5 w-5 text-teal-600 focus:ring-teal-500 rounded border-gray-300"
          />
          <span className="text-sm font-medium text-gray-700">
            I understand and agree to the Data Usage and Confidentiality terms.
          </span>
        </label>
        
        <label className="flex items-start space-x-3">
          <input 
            type="checkbox" 
            checked={agreedAI} 
            onChange={(e) => setAgreedAI(e.target.checked)}
            className="mt-1 h-5 w-5 text-teal-600 focus:ring-teal-500 rounded border-gray-300"
          />
          <span className="text-sm font-medium text-gray-700">
            I acknowledge the platform utilizes AI and agree to have my inputs processed by it.
          </span>
        </label>

        <div className="pt-4">
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'I Agree & Continue'}
          </button>
        </div>
      </form>
    </div>
  );
}
