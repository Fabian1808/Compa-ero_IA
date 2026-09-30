import { NavLink, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  Settings, 
  FileText, 
  BarChart3,
  Shield,
  Menu,
  X,
  ChevronDown
} from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/store/authStore';

const adminNavigation = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Métricas', href: '/admin/metrics', icon: BarChart3 },
  { name: 'Tenants', href: '/admin/tenants', icon: Building2 },
  { name: 'Usuarios', href: '/admin/users', icon: Users },
  { name: 'Audit Logs', href: '/admin/audit-logs', icon: FileText },
  { name: 'Configuración', href: '/admin/settings', icon: Settings },
  { name: 'Seguridad', href: '/admin/security', icon: Shield },
];

export function AdminSidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) return null;

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="lg:hidden fixed top-4 left-4 z-50"
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? 'Cerrar menú' : 'Abrir menú'}
      >
        {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Navegación administración"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Shield className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Admin Panel</h1>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Administración del sistema</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Navegación admin">
            {adminNavigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
                  }`
                }
                onClick={() => {
                  if (window.innerWidth < 1024) toggleSidebar();
                }}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                  {useAuthStore.getState().user?.name?.charAt(0).toUpperCase() || 'A'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                  {useAuthStore.getState().user?.name || 'Admin'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                  {useAuthStore.getState().user?.email || ''}
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
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