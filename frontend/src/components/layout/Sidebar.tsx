import { NavLink } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import {
  Home,
  CheckSquare,
  FolderKanban,
  Calendar,
  Brain,
  Settings,
  Menu,
  X,
  Puzzle,
  LayoutDashboard,
  Shield,
  Building2,
  Users,
  FileText,
  UserCircle2
} from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/store/authStore';
import { useI18n } from '@/i18n';

/**
 * Main menu.
 *
 * `labelKey` points at the catalog so the official wording lives in one place.
 * Existing routes are reused rather than renamed, so the official menu is
 * surfaced without breaking deep links or bookmarks.
 */
const navigation = [
  { labelKey: 'nav.home', href: '/', icon: Home },
  { labelKey: 'nav.myWork', href: '/tasks', icon: CheckSquare },
  { labelKey: 'nav.projects', href: '/projects', icon: FolderKanban },
  { labelKey: 'nav.people', href: '/workmap', icon: UserCircle2 },
  { labelKey: 'nav.calendar', href: '/calendar', icon: Calendar },
  { labelKey: 'nav.memory', href: '/memory', icon: Brain },
  { labelKey: 'nav.connections', href: '/connectors', icon: Puzzle },
  { labelKey: 'nav.settings', href: '/settings', icon: Settings },
];

/**
 * Admin links follow the server-decided flag.
 *
 * `GET /auth/me` resolves the caller's tenant membership and ships `is_admin`;
 * the client must not re-derive it from the role string, because that is how
 * these links would end up visible to members who then get a 403 from the API.
 */
const adminNavigation = [
  { labelKey: 'admin.dashboard', href: '/admin', icon: LayoutDashboard },
  { labelKey: 'admin.tenants', href: '/admin/tenants', icon: Building2 },
  { labelKey: 'admin.users', href: '/admin/users', icon: Users },
  { labelKey: 'admin.metrics', href: '/admin/metrics', icon: FileText },
  { labelKey: 'admin.auditLogs', href: '/admin/audit-logs', icon: FileText },
  { labelKey: 'admin.settings', href: '/admin/settings', icon: Settings },
  { labelKey: 'admin.security', href: '/admin/security', icon: Shield },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isAdmin = useAuthStore((state) => state.isAdmin);
  const { t } = useI18n();

  if (!isAuthenticated) return null;

  const navLinkClass = (isActive: boolean, admin: boolean) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? admin
          ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
          : 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
        : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
    }`;

  const handleNavigate = () => {
    if (window.innerWidth < 1024) toggleSidebar();
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="lg:hidden fixed top-4 left-4 z-50"
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? t('nav.close') : t('nav.open')}
      >
        {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label={t('nav.main')}
      >
        <div className="flex flex-col h-full">
          <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-700">
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
              {t('app.name')}
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">{t('app.tagline')}</p>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label={t('nav.main')}>
            {navigation.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) => navLinkClass(isActive, false)}
                onClick={handleNavigate}
                end={item.href === '/'}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {t(item.labelKey)}
              </NavLink>
            ))}

            {isAdmin && (
              <>
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="px-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    {t('admin.section')}
                  </p>
                </div>
                {adminNavigation.map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    className={({ isActive }) => navLinkClass(isActive, true)}
                    onClick={handleNavigate}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                    {t(item.labelKey)}
                  </NavLink>
                ))}
              </>
            )}
          </nav>

          <div className="p-3 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                  {user?.name || t('nav.userFallback')}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email || ''}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {sidebarOpen && window.innerWidth < 1024 && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}
    </>
  );
}