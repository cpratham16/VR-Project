import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const PATIENT_NAV: NavItem[] = [
  { to: '/patient/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/patient/screening', label: 'Screening', icon: '📝' },
  { to: '/patient/mood', label: 'Mood Tracker', icon: '🌿' },
  { to: '/patient/community', label: 'Community', icon: '💬' },
  { to: '/patient/appointments', label: 'Appointments', icon: '📅' },
  { to: '/patient/vr', label: 'VR Therapy', icon: '🥽' },
  { to: '/patient/chat', label: 'AI Companion', icon: '🤖' },
];

const DOCTOR_NAV: NavItem[] = [
  { to: '/doctor/dashboard', label: 'Triage Dashboard', icon: '🩺' },
  { to: '/doctor/vr', label: 'VR Assignments', icon: '🥽' },
  { to: '/doctor/moderation', label: 'Moderation Queue', icon: '🛡️' },
  { to: '/doctor/appointments', label: 'Doctor Calendar', icon: '📅' },
];

const ADMIN_NAV: NavItem[] = [
  { to: '/admin/doctors', label: 'Doctor Approvals', icon: '🪪' },
  { to: '/admin/dashboard', label: 'Admin Panel', icon: '📊' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  const navItems: NavItem[] = [
    ...(user?.role === 'patient' ? PATIENT_NAV : []),
    ...(user?.role === 'doctor' || user?.role === 'admin' ? DOCTOR_NAV : []),
    ...(user?.role === 'admin' ? ADMIN_NAV : []),
  ];

  const itemCls = ({ isActive }: { isActive: boolean }) =>
    `group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium tracking-[0.02em] transition-colors duration-200 ${
      isActive
        ? 'bg-accent-muted text-accent'
        : 'text-[#cfc8bd] hover:bg-white/5 hover:text-white'
    } ${collapsed ? 'justify-center px-2' : ''}`;

  const iconCls = 'inline-block w-5 shrink-0 text-center text-base leading-none';

  const sidebarBody = (
    <>
      <div className={`flex h-16 shrink-0 items-center border-b border-white/10 ${collapsed ? 'justify-center px-2' : 'justify-between px-4'}`}>
        <Link
          to={user ? navItems[0]?.to ?? '/' : '/'}
          className="group flex items-center gap-2.5"
          aria-label="Mindora home"
          onClick={onMobileClose}
        >
          <span
            aria-hidden="true"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-white/10 text-lg transition-colors duration-200 group-hover:bg-accent"
          >
            🧠
          </span>
          {!collapsed && <span className="font-display text-lg font-bold tracking-normal text-white">Mindora</span>}
        </Link>
        <div className="flex items-center gap-1">
          <button
            onClick={onToggle}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="hidden cursor-pointer rounded-md p-1.5 text-[#cfc8bd] transition-colors hover:bg-white/10 hover:text-white lg:block"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              {collapsed ? (
                <path
                  fillRule="evenodd"
                  d="M6.72 8.53a.75.75 0 010-1.06l2.25-2.25a.75.75 0 011.06 1.06L8.31 8l1.72 1.72a.75.75 0 01-1.06 1.06l-2.25-2.25zm4 0a.75.75 0 010-1.06l2.25-2.25a.75.75 0 011.06 1.06L12.31 8l1.72 1.72a.75.75 0 01-1.06 1.06l-2.25-2.25z"
                  clipRule="evenodd"
                />
              ) : (
                <path
                  fillRule="evenodd"
                  d="M13.28 11.47a.75.75 0 010 1.06l-2.25 2.25a.75.75 0 01-1.06-1.06l1.72-1.72-1.72-1.72a.75.75 0 011.06-1.06l2.25 2.25zm-4 0a.75.75 0 010 1.06l-2.25 2.25a.75.75 0 01-1.06-1.06l1.72-1.72-1.72-1.72a.75.75 0 011.06-1.06l2.25 2.25z"
                  clipRule="evenodd"
                />
              )}
            </svg>
          </button>
          {!collapsed && (
            <button
              onClick={onMobileClose}
              aria-label="Close sidebar"
              className="cursor-pointer rounded-md p-1.5 text-[#cfc8bd] transition-colors hover:bg-white/10 hover:text-white lg:hidden"
            >
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <nav aria-label="Sidebar" className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <p className={`px-3 pb-2 font-mono text-[10px] font-medium uppercase tracking-[0.14em] text-white/40 ${collapsed ? 'hidden' : ''}`}>
          Menu
        </p>
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} className={itemCls} title={collapsed ? item.label : undefined} onClick={onMobileClose}>
            <span aria-hidden="true" className={iconCls}>
              {item.icon}
            </span>
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className={`shrink-0 space-y-1 border-t border-white/10 px-3 py-4 ${collapsed ? 'flex flex-col items-center' : ''}`}>
        <NavLink
          to="/account/profile"
          className={itemCls}
          title={collapsed ? 'My Profile' : undefined}
          onClick={onMobileClose}
        >
          <span aria-hidden="true" className={iconCls}>
            ⚙️
          </span>
          {!collapsed && <span>My Profile</span>}
        </NavLink>
        <button
          onClick={handleLogout}
          className={`group flex w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm font-medium tracking-[0.02em] text-[#cfc8bd] transition-colors duration-200 hover:bg-red-500/10 hover:text-red-300 ${
            collapsed ? 'justify-center px-2' : ''
          }`}
          title={collapsed ? 'Log out' : undefined}
        >
          <span aria-hidden="true" className={iconCls}>
            🚪
          </span>
          {!collapsed && <span>Log out</span>}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden shrink-0 flex-col bg-[#161513] transition-[width] duration-300 ease-in-out lg:flex ${
          collapsed ? 'w-16' : 'w-64'
        }`}
      >
        {sidebarBody}
      </aside>

      {/* Mobile overlay sidebar */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-50 flex bg-black/50 backdrop-blur-sm lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
          onClick={onMobileClose}
        >
          <aside
            className="flex h-full w-72 shrink-0 flex-col bg-[#161513] shadow-2xl motion-safe:animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarBody}
          </aside>
        </div>
      )}
    </>
  );
}