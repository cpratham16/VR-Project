import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Patient Dashboard</h2>
        <button onClick={handleLogout} className="px-4 py-2 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50">
          Logout
        </button>
      </div>
      
      <div className="bg-teal-50 border border-teal-100 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-teal-800 mb-2">Welcome Back!</h3>
        <p className="text-gray-700">Email: {user?.email}</p>
        <p className="text-gray-700">Role: {user?.role}</p>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border border-gray-200 p-4 rounded-lg shadow-sm">
          <h4 className="font-semibold text-lg text-gray-800">Mood Tracker</h4>
          <p className="text-sm text-gray-500 mt-1">Log daily mood, tag influencing factors, and view trends.</p>
          <button 
            onClick={() => navigate('/patient/mood')}
            className="mt-3 w-full py-2 bg-teal-600 text-white rounded hover:bg-teal-700 font-medium transition"
          >
            Daily Check-In & Journal
          </button>
        </div>
        <div className="border border-gray-200 p-4 rounded-lg shadow-sm">
          <h4 className="font-semibold text-lg text-gray-800">My Assessments</h4>
          <p className="text-sm text-gray-500 mt-1">Take a mental health screening (PHQ-9 / GAD-7) or view past results.</p>
          <button 
            onClick={() => navigate('/patient/screening')}
            className="mt-3 w-full py-2 bg-teal-600 text-white rounded hover:bg-teal-700 font-medium transition"
          >
            Start Assessment / History
          </button>
        </div>
        <div className="border border-gray-200 p-4 rounded-lg shadow-sm">
          <h4 className="font-semibold text-lg text-gray-800">Appointments</h4>
          <p className="text-sm text-gray-500 mt-1">Schedule a session with a campus counselor or doctor.</p>
          <button 
            onClick={() => navigate('/patient/appointments')}
            className="mt-3 w-full py-2 bg-teal-600 text-white rounded hover:bg-teal-700 font-medium transition"
          >
            Book / View Schedule
          </button>
        </div>
        <div className="border border-indigo-100 p-4 rounded-lg shadow-sm">
          <h4 className="font-semibold text-lg text-gray-800">🥽 VR Therapy</h4>
          <p className="text-sm text-gray-500 mt-1">Access your doctor-assigned browser-based VR exposure therapy.</p>
          <button
            onClick={() => navigate('/patient/vr')}
            className="mt-3 w-full py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium transition"
          >
            Launch VR Center
          </button>
        </div>
      </div>
    </div>
  );
}
