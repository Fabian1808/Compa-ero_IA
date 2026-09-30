import { NavLink, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import { 
  Home, 
  CheckSquare, 
  FolderKanban, 
  Calendar, 
  Clock, 
  Flag,
  Brain, 
  Settings,
  Menu,
  X,
  Bell,
  Moon,
  Sun,
  GitBranch,
  AlertTriangle,
  Puzzle,
  LayoutDashboard,
  Shield,
  Building2,
  Users,
  FileText
} from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/store/authStore';

const navigation = [
  { name: 'Inicio', href: '/', icon: Home },
  { name: 'Pendientes', href: '/tasks', icon: CheckSquare },
  { name: 'Proyectos', href: '/projects', icon: FolderKanban },
  { name: 'Mapa de Trabajo', href: '/workmap', icon: GitBranch },
  { name: 'Calendario', href: '/calendar', icon: Calendar },
  { name: 'Seguimientos', href: '/followups', icon: Clock },
  { name: 'Compromisos', href: '/commitments', icon: Flag },
  { name: 'Deadlines', href: '/deadlines', icon: Clock },
  { name: 'Memoria', href: '/memory', icon: Brain },
  { name: 'Conectores', href: '/connectors', icon: Puzzle },
  { name: 'Aplicaciones', href: '/apps', icon: Settings },
  { name: 'Configuración', href: '/settings', icon: Settings },
];

const adminNavigation = [
  { name: 'Panel Admin', href: '/admin', icon: LayoutDashboard },
  { name: 'Tenants', href: '/admin/tenants', icon: Building2 },
  { name: 'Usuarios', href: '/admin/users', icon: Users },
  { name: 'Métricas', href: '/admin/metrics', icon: FileText },
  { name: 'Audit Logs', href: '/admin/audit-logs', icon: FileText },
  { name: 'Configuración', href: '/admin/settings', icon: Settings },
  { name: 'Seguridad', href: '/admin/security', icon: FileText },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) return null;

  const isAdmin = user?.role === 'admin' || user?.role === 'owner';

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
        aria-label="Navegación principal"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-700">
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">AI Workmate</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Navegación">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
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

            {isAdmin && (
              <>
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="px-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Administración
                  </p>
                </div>
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
              </>
            )}
          </nav>

          {/* Footer */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                  {useAuthStore.getState().user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                  {useAuthStore.getState().user?.name || 'Usuario'}
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