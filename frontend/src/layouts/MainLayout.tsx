import { Outlet, Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PanicModal from '../components/PanicModal';

export default function MainLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `font-medium ${isActive ? 'text-blue-600' : 'text-gray-700 hover:text-blue-600'}`;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg focus:text-blue-700 font-semibold"
      >
        Skip to main content
      </a>
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span aria-hidden="true" className="text-2xl">🥽</span>
            <span className="text-xl font-bold text-gray-900">VR MindHealth</span>
          </Link>

          <nav aria-label="Primary" className="flex items-center gap-6">
            {user ? (
              <>
                {user.role === 'patient' && (
                  <>
                    <NavLink to="/patient/dashboard" className={navLinkClass}>Dashboard</NavLink>
                    <NavLink to="/patient/screening" className={navLinkClass}>Screening</NavLink>
                    <NavLink to="/patient/mood" className={navLinkClass}>Mood Tracker</NavLink>
                    <NavLink to="/patient/community" className={navLinkClass}>Community</NavLink>
                    <NavLink to="/patient/vr" className="text-indigo-600 font-semibold hover:text-indigo-800 flex items-center gap-1">
                      <span aria-hidden="true">🥽</span> VR Therapy
                    </NavLink>
                    <NavLink to="/patient/chat" className="text-indigo-600 font-semibold hover:text-indigo-800 flex items-center gap-1">
                      <span aria-hidden="true">🤖</span> AI Companion
                    </NavLink>
                    <NavLink to="/patient/appointments" className={navLinkClass}>Appointments</NavLink>
                  </>
                )}

                {(user.role === 'doctor' || user.role === 'admin') && (
                  <>
                    <NavLink to="/doctor/dashboard" className={navLinkClass}>Triage Dashboard</NavLink>
                    <NavLink to="/doctor/vr" className="text-indigo-700 hover:text-indigo-900 font-medium">VR Assignments</NavLink>
                    <NavLink to="/doctor/moderation" className="text-amber-700 hover:text-amber-900 font-medium">Moderation Queue</NavLink>
                    <NavLink to="/doctor/appointments" className={navLinkClass}>Doctor Calendar</NavLink>
                  </>
                )}

                {user.role === 'admin' && (
                  <NavLink to="/admin/dashboard" className="bg-purple-100 text-purple-800 hover:bg-purple-200 font-semibold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1">
                    <span aria-hidden="true">📊</span> Admin Panel
                  </NavLink>
                )}

                <PanicModal />

                <button
                  onClick={handleLogout}
                  aria-label="Log out"
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium px-3 py-1 rounded border border-gray-300"
                >
                  Logout
                </button>
              </>
            ) 
              : (
              <>
                <Link to="/auth/login" className="text-gray-700 hover:text-blue-600 font-medium">Login</Link>
                <Link to="/auth/signup" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700">Sign Up</Link>
                <PanicModal />
              </>
            )}
          </nav>
        </div>
      </header>
      <main id="main-content" className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
