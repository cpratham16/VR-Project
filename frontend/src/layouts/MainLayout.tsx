import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import AppHeader from '../components/AppHeader';
import { useAuth } from '../contexts/AuthContext';
import PanicModal from '../components/PanicModal';
import AssessmentReminderModal from '../components/AssessmentReminderModal';
import { useScreeningReminder, type ScreeningType } from '../hooks/useScreeningReminder';

const COLLAPSE_KEY = 'mindora-sidebar-collapsed';

function PublicHeader() {
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3.5 py-2 text-sm font-medium tracking-[0.02em] transition-colors duration-200 ${
      isActive ? 'text-accent' : 'text-muted-foreground hover:text-foreground'
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-[#e8e4df] bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5" aria-label="Mindora home">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 items-center justify-center rounded-md border border-[#e8e4df] bg-white text-lg shadow-sm"
          >
            🧠
          </span>
          <span className="font-display text-lg font-bold tracking-normal text-foreground">Mindora</span>
        </Link>
        <nav aria-label="Public navigation" className="flex items-center gap-1">
          <NavLink to="/" className={linkCls} end>
            Home
          </NavLink>
          <NavLink to="/auth/login" className={linkCls}>
            Login
          </NavLink>
          <NavLink to="/auth/signup" className={linkCls}>
            Create account
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default function MainLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState<boolean>(() => localStorage.getItem(COLLAPSE_KEY) === '1');
  const [mobileOpen, setMobileOpen] = useState(false);

  const isPatient = user?.role === 'patient';
  const { dueTypes, skipToday, takeLater } = useScreeningReminder(isPatient && !!user);

  const handleScreeningNavigate = (type?: ScreeningType) => {
    takeLater();
    navigate(type ? `/patient/screening?type=${encodeURIComponent(type)}` : '/patient/screening');
  };

  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0');
  }, [collapsed]);

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-background">
        <PublicHeader />
        <main id="main-content" className="flex-1">
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-[60] focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:font-semibold focus:text-accent focus:shadow-lg focus:ring-2 focus:ring-accent"
      >
        Skip to main content
      </a>

      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((prev) => !prev)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader onOpenMobileSidebar={() => setMobileOpen(true)} />

        <main id="main-content" className="flex-1">
          <Outlet />
        </main>
      </div>

      {user.role === 'patient' && (
        <div className="fixed bottom-4 left-4 z-40">
          <PanicModal />
        </div>
      )}

      {isPatient && (
        <AssessmentReminderModal
          dueTypes={dueTypes}
          onTakeNow={handleScreeningNavigate}
          onTakeLater={takeLater}
          onSkip={skipToday}
        />
      )}
    </div>
  );
}