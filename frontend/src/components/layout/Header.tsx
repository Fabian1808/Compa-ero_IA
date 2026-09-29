import { useUIStore } from '@/store/uiStore';
import { useNotifications } from '@/hooks/useNotifications';
import { useAuthStore } from '@/store/authStore';
import { Bell, Moon, Sun, LogOut, User } from 'lucide-react';
import { Button } from '@/components/ui';
import { Badge } from '@/components/ui';
import { formatRelativeTime } from '@/utils/formatters';

export function Header() {
  const { theme, setTheme } = useUIStore();
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const { user, logout } = useAuthStore();

  const toggleTheme = () => {
    const themes: ('light' | 'dark' | 'system')[] = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme);
    setTheme(themes[(currentIndex + 1) % themes.length]);
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Left side - empty for now, sidebar toggle is in Sidebar component */}

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className="relative"
              aria-label={`Notificaciones${unreadCount > 0 ? `, ${unreadCount} sin leer` : ''}`}
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>

            {/* Notification dropdown */}
            <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg py-2 z-50">
              <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">Notificaciones</h3>
                {unreadCount > 0 && (
                  <Badge variant="primary">{unreadCount} nuevas</Badge>
                )}
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.slice(0, 10).map((notification) => (
                  <button
                    key={notification.id}
                    onClick={() => markAsRead(notification.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                      !notification.is_read ? 'bg-slate-50 dark:bg-slate-700/30' : ''
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{notification.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">{notification.message}</p>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{formatRelativeTime(notification.created_at)}</p>
                  </button>
                ))}
                {notifications.length === 0 && (
                  <div className="px-4 py-8 text-center text-slate-500 dark:text-slate-400 text-sm">
                    No hay notificaciones
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            aria-label={`Tema actual: ${theme}. Click para cambiar.`}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>

          {/* User menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className="gap-2"
              aria-label="Menú de usuario"
            >
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <User className="h-4 w-4 text-primary-700 dark:text-primary-300" />
              </div>
              <span className="hidden sm:block text-sm font-medium text-slate-700 dark:text-slate-300">
                {user?.name || 'Usuario'}
              </span>
            </Button>

            <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg py-2 z-50">
              <button
                onClick={logout}
                className="w-full px-4 py-2 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}