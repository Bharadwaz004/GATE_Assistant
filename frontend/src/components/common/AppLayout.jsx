/**
 * Dashboard shell — sidebar + outlet for page content.
 */
import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, CalendarDays, Users, LogOut,
  Menu, X, Flame, GraduationCap,
} from 'lucide-react';
import useStore from '../../store/useStore';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/plan', icon: CalendarDays, label: 'Study Plan' },
  { to: '/matches', icon: Users, label: 'Study Partners' },
];

export default function AppLayout() {
  const { sidebarOpen, toggleSidebar, logout, profile, streak } = useStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ───────────────────────────────────────── */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-30 flex flex-col bg-surface-950 text-white transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-[72px]'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 h-16 border-b border-white/10">
          <GraduationCap className="w-7 h-7 text-brand-400 flex-shrink-0" />
          {sidebarOpen && (
            <span className="font-display text-lg tracking-tight truncate">
              GATE Planner
            </span>
          )}
          <button
            onClick={toggleSidebar}
            className="ml-auto p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 py-4 space-y-1 px-3">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-brand-500/20 text-brand-300'
                    : 'text-surface-400 hover:bg-white/5 hover:text-white'
                )
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Streak badge */}
        {streak && (
          <div className={clsx('mx-3 mb-3 p-3 rounded-xl bg-gradient-to-br from-brand-600/30 to-brand-800/20 border border-brand-500/20', !sidebarOpen && 'flex justify-center')}>
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-brand-400 animate-bounce-subtle" />
              {sidebarOpen && (
                <div>
                  <div className="text-xs text-brand-300 font-semibold">Streak</div>
                  <div className="text-lg font-bold text-white leading-tight">
                    {streak.current_streak} days
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* User + Logout */}
        <div className="border-t border-white/10 p-3">
          <button
            onClick={handleLogout}
            className={clsx(
              'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-surface-400',
              'hover:bg-white/5 hover:text-white transition-colors'
            )}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Log out</span>}
          </button>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────── */}
      <main
        className={clsx(
          'flex-1 overflow-y-auto transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-[72px]'
        )}
      >
        <div className="max-w-6xl mx-auto px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
