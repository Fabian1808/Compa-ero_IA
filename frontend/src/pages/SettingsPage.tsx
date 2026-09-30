import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useNotifications } from '@/hooks/useNotifications';
import { useUIStore } from '@/store/uiStore';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Separator } from '@/components/ui';
import { Bell, Moon, Sun, Monitor, LogOut, User, Key, Database, RefreshCw, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import { useI18n } from '@/i18n/I18nProvider';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { settings, updateSettings, fetchSettings } = useNotifications();
  const { theme, setTheme } = useUIStore();
  const { t, locale, setLocale } = useI18n();
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'account' | 'advanced'>('general');
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');

  const tabs = [
    { id: 'general', label: t('pages.settings.sections.general'), icon: Monitor },
    { id: 'notifications', label: t('pages.settings.sections.notifications'), icon: Bell },
    { id: 'account', label: t('pages.settings.sections.account'), icon: User },
    { id: 'advanced', label: t('pages.settings.sections.advanced'), icon: Database },
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
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t('pages.settings.title')}</h1>
        <p className="text-slate-500 dark:text-slate-400">{t('pages.settings.subtitle')}</p>
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
              {t('pages.settings.sections.general')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">{t('pages.settings.sections.theme')}</label>
              <div className="grid grid-cols-3 gap-3">
                {(['light', 'dark', 'system'] as const).map((themeName) => (
                  <Button
                    key={themeName}
                    variant={theme === themeName ? 'primary' : 'secondary'}
                    className="h-20 flex flex-col gap-2"
                    onClick={() => handleThemeChange(themeName)}
                  >
                    {themeName === 'light' && <Sun className="h-6 w-6 mx-auto" />}
                    {themeName === 'dark' && <Moon className="h-6 w-6 mx-auto" />}
                    {themeName === 'system' && <Monitor className="h-6 w-6 mx-auto" />}
                    <span className="text-sm">{t(`pages.settings.themes.${themeName}`)}</span>
                  </Button>
                ))}
              </div>
            </div>

            <Separator />

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">{t('pages.settings.sections.language')}</label>
              <select
                className="input w-full max-w-xs"
                value={locale}
                onChange={(e) => setLocale(e.target.value as typeof locale)}
              >
                <option value="es-PE">{t('pages.settings.languages.es')}</option>
                <option value="en-US">{t('pages.settings.languages.en')}</option>
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
              {t('pages.settings.sections.notifications')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.notifications.enabled')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.notifications.receiveImportant')}</p>
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
                <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.notifications.focusMode')}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.notifications.focusModeHint')}</p>
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
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.notifications.dailyBriefing')}</label>
                <select
                  value={settings.daily_briefing_hour}
                  onChange={(e) => handleNotificationChange('daily_briefing_hour', parseInt(e.target.value))}
                  className="input"
                >
                  {[6,7,8,9,10].map(h => <option key={h} value={h}>{h}:00</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.notifications.endOfDay')}</label>
                <select
                  value={settings.end_of_day_hour}
                  onChange={(e) => handleNotificationChange('end_of_day_hour', parseInt(e.target.value))}
                  className="input"
                >
                  {[16,17,18,19,20].map(h => <option key={h} value={h}>{h}:00</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.notifications.deadlines')}</label>
                <Input
                  type="number"
                  value={settings.deadline_reminder_minutes_before}
                  onChange={(e) => handleNotificationChange('deadline_reminder_minutes_before', parseInt(e.target.value))}
                  min="0"
                  max="1440"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.notifications.meetings')}</label>
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
              {t('pages.settings.sections.account')}
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
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{t('pages.settings.account.id')}: {user.id.slice(0, 8)}...</p>
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.fields.name')}</label>
                <Input value={user.name} readOnly />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('pages.settings.fields.email')}</label>
                <Input value={user.email} readOnly type="email" />
              </div>
            </div>

            <Separator />

            <Button variant="destructive" onClick={logout} className="w-full">
              <LogOut className="h-4 w-4" />
              {t('pages.settings.account.logout')}
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
                {t('pages.settings.sections.data')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.data.autoSync')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.data.autoSyncHint')}</p>
                </div>
                <Button variant="secondary" onClick={handleSync} loading={syncStatus === 'syncing'}>
                  <RefreshCw className="h-4 w-4" />
                  {t('pages.settings.data.syncNow')}
                </Button>
              </div>
              
              {syncStatus === 'success' && (
                <div className="text-sm text-green-600 dark:text-green-400">{t('pages.settings.data.syncCompleted')}</div>
              )}
              {syncStatus === 'error' && (
                <div className="text-sm text-red-600 dark:text-red-400">{t('pages.settings.data.syncFailed')}</div>
              )}

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.data.export')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.data.exportHint')}</p>
                </div>
                <Button variant="secondary">
                  {t('pages.settings.data.exportJson')}
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.data.clear')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.data.clearHint')}</p>
                </div>
                <Button variant="destructive">
                  {t('pages.settings.data.clearAll')}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                {t('pages.settings.sections.ai')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.ai.localProcessing')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.ai.local')}</p>
                </div>
                <span className="badge badge-success">{t('pages.settings.states.active')}</span>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.ai.semanticMemory')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.ai.localEmbeddings')}</p>
                </div>
                <span className="badge badge-success">{t('pages.settings.states.active')}</span>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">{t('pages.settings.ai.sendData')}</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('pages.settings.ai.sendDataHint')}</p>
                </div>
                <span className="badge badge-warning">{t('pages.settings.states.controlled')}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-200 dark:border-red-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-5 w-5" />
                {t('pages.settings.sections.danger')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" className="w-full">
                {t('pages.settings.danger.deleteAccount')}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}