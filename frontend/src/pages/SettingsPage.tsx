import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useNotifications } from '@/hooks/useNotifications';
import { useUIStore } from '@/store/uiStore';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Separator } from '@/components/ui';
import { Bell, Moon, Sun, Monitor, LogOut, User, Key, Database, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { settings, updateSettings, fetchSettings } = useNotifications();
  const { theme, setTheme } = useUIStore();
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'account' | 'advanced'>('general');
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');

  const tabs = [
    { id: 'general', label: 'General', icon: Monitor },
    { id: 'notifications', label: 'Notificaciones', icon: Bell },
    { id: 'account', label: 'Cuenta', icon: User },
    { id: 'advanced', label: 'Avanzado', icon: Database },
  ];

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
  };

  const handleSync = async () => {
    setSyncStatus('syncing');
    try {
      // In a real app, this would trigger the sync
      await new Promise(resolve => setTimeout(resolve, 1500));
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 2000);
    } catch {
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 2000);
    }
  };

  const handleNotificationChange = async (key: keyof typeof settings, value: boolean | number) => {
    if (!settings) return;
    await updateSettings({ [key]: value });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Configuración</h1>
        <p className="text-slate-500 dark:text-slate-400">Personaliza tu experiencia en AI Workmate</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'primary' : 'ghost'}
            size="sm"
            className="flex-1 gap-2"
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </Button>
        ))}
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              General
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Tema</label>
              <div className="grid grid-cols-3 gap-3">
                {(['light', 'dark', 'system'] as const).map((t) => (
                  <Button
                    key={t}
                    variant={theme === t ? 'primary' : 'secondary'}
                    className="h-20 flex flex-col gap-2"
                    onClick={() => handleThemeChange(t)}
                  >
                    {t === 'light' && <Sun className="h-6 w-6 mx-auto" />}
                    {t === 'dark' && <Moon className="h-6 w-6 mx-auto" />}
                    {t === 'system' && <Monitor className="h-6 w-6 mx-auto" />}
                    <span className="capitalize text-sm">{t}</span>
                  </Button>
                ))}
              </div>
            </div>

            <Separator />

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Idioma</label>
              <select className="input w-full max-w-xs" defaultValue="es">
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && settings && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notificaciones
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-slate-900 dark:text-slate-100">Activar notificaciones</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">Recibir alertas importantes</p>
              </div>
              <Input
                type="checkbox"
                checked={settings.enabled}
                onChange={(e) => handleNotificationChange('enabled', e.target.checked)}
                className="w-12 h-6"
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-slate-900 dark:text-slate-100">Modo enfoque silencia no críticas</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">Solo mostrar alertas críticas durante el modo enfoque</p>
              </div>
              <Input
                type="checkbox"
                checked={settings.focus_mode_silence_non_critical}
                onChange={(e) => handleNotificationChange('focus_mode_silence_non_critical', e.target.checked)}
                className="w-12 h-6"
              />
            </div>

            <Separator />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Briefing diario a las</label>
                <select
                  value={settings.daily_briefing_hour}
                  onChange={(e) => handleNotificationChange('daily_briefing_hour', parseInt(e.target.value))}
                  className="input"
                >
                  {[6,7,8,9,10].map(h => <option key={h} value={h}>{h}:00</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Cierre del día a las</label>
                <select
                  value={settings.end_of_day_hour}
                  onChange={(e) => handleNotificationChange('end_of_day_hour', parseInt(e.target.value))}
                  className="input"
                >
                  {[16,17,18,19,20].map(h => <option key={h} value={h}>{h}:00</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Recordar deadlines (min antes)</label>
                <Input
                  type="number"
                  value={settings.deadline_reminder_minutes_before}
                  onChange={(e) => handleNotificationChange('deadline_reminder_minutes_before', parseInt(e.target.value))}
                  min="0"
                  max="1440"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Recordar reuniones (min antes)</label>
                <Input
                  type="number"
                  value={settings.meeting_reminder_minutes_before}
                  onChange={(e) => handleNotificationChange('meeting_reminder_minutes_before', parseInt(e.target.value))}
                  min="0"
                  max="1440"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Account Tab */}
      {activeTab === 'account' && user && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Cuenta
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <span className="text-2xl font-bold text-primary-700 dark:text-primary-300">
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{user.name}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">{user.email}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">ID: {user.id.slice(0, 8)}...</p>
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre</label>
                <Input value={user.name} readOnly />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
                <Input value={user.email} readOnly type="email" />
              </div>
            </div>

            <Separator />

            <Button variant="destructive" onClick={logout} className="w-full">
              <LogOut className="h-4 w-4" />
              Cerrar sesión
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Advanced Tab */}
      {activeTab === 'advanced' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Datos y sincronización
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Sincronización automática</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Cada 5 minutos</p>
                </div>
                <Button variant="secondary" onClick={handleSync} loading={syncStatus === 'syncing'}>
                  <RefreshCw className="h-4 w-4" />
                  Sincronizar ahora
                </Button>
              </div>
              
              {syncStatus === 'success' && (
                <div className="text-sm text-green-600 dark:text-green-400">Sincronización completada</div>
              )}
              {syncStatus === 'error' && (
                <div className="text-sm text-red-600 dark:text-red-400">Error en la sincronización</div>
              )}

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Exportar datos</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Descargar todas tus tareas y proyectos</p>
                </div>
                <Button variant="secondary">
                  Exportar JSON
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Borrar todos los datos</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Eliminar tareas, proyectos e historial (irreversible)</p>
                </div>
                <Button variant="destructive">
                  Borrar todo
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                IA y privacidad
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Procesamiento local</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Usar Ollama local (phi3:3.8b)</p>
                </div>
                <span className="badge badge-success">Activo</span>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Memoria semántica</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Almacenar embeddings localmente (Qdrant)</p>
                </div>
                <span className="badge badge-success">Activo</span>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">Enviar datos a IA</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Solo se envía texto necesario para análisis</p>
                </div>
                <span className="badge badge-warning">Controlado</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-200 dark:border-red-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-5 w-5" />
                Zona de peligro
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" className="w-full">
                Eliminar cuenta y todos los datos
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}