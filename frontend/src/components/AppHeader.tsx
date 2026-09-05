import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface AppHeaderProps {
  onOpenMobileSidebar: () => void;
}

export default function AppHeader({ onOpenMobileSidebar }: AppHeaderProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const dashboardPath =
    user?.role === 'patient'
      ? '/patient/dashboard'
      : user?.role === 'doctor' || user?.role === 'admin'
        ? '/doctor/dashboard'
        : '/';

  const initials = (user?.full_name || user?.email || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');

  const roleLabel =
    user?.role === 'patient'
      ? 'Patient'
      : user?.role === 'doctor'
        ? 'Doctor'
        : user?.role === 'admin'
          ? 'Administrator'
          : '';

  return (
    <header className="sticky top-0 z-40 border-b border-[#e8e4df] bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-2">
          <button
            onClick={onOpenMobileSidebar}
            aria-label="Open navigation menu"
            className="cursor-pointer rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path
                fillRule="evenodd"
                d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 5A.75.75 0 012.75 9.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 9.75zm0 5a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75a.75.75 0 01-.75-.75z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          <Link
            to={dashboardPath}
            className="flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <span aria-hidden="true" className="text-base">
              ←
            </span>
            Back to Dashboard
          </Link>

          {user && (
            <span
              aria-hidden="true"
              className="hidden h-4 w-px bg-[#e8e4df] sm:block"
            />
          )}
          {user && (
            <span className="hidden truncate font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground sm:block">
              {roleLabel} Panel
            </span>
          )}
        </div>

        <div className="relative flex shrink-0 items-center gap-2">
          <button
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-label="Account menu"
            className="flex cursor-pointer items-center gap-2 rounded-full border border-[#e8e4df] bg-white py-1 pl-1 pr-3 shadow-sm transition-all duration-200 hover:border-accent hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <span
              aria-hidden="true"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-accent font-mono text-xs font-bold uppercase tracking-wide text-white"
            >
              {initials || '?'}
            </span>
            <span className="hidden max-w-[140px] truncate text-sm font-medium text-foreground sm:block">
              {user?.full_name || user?.email}
            </span>
          </button>

          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 top-full mt-2 w-52 overflow-hidden rounded-md border border-[#e8e4df] bg-white py-1 shadow-lg"
            >
              <div className="border-b border-[#e8e4df] px-4 py-2.5">
                <p className="truncate text-sm font-medium text-foreground">{user?.full_name || user?.email}</p>
                <p className="truncate font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  {user?.email}
                </p>
              </div>
              <button
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  navigate('/account/profile');
                }}
                className="block w-full cursor-pointer px-4 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                My Profile & Info
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}