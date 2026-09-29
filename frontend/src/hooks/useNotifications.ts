import { useCallback, useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { Notification, NotificationSettings } from '@/types/api';

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getNotifications({ limit: 50 });
      setNotifications(data);
      setUnreadCount(data.filter((n) => !n.is_read).length);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await api.getNotificationSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to fetch notification settings:', err);
    }
  }, []);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  }, []);

  const updateSettings = useCallback(async (newSettings: Partial<NotificationSettings>) => {
    if (!settings) return;
    try {
      const updated = await api.updateNotificationSettings({ ...settings, ...newSettings });
      setSettings(updated);
    } catch (err) {
      console.error('Failed to update notification settings:', err);
    }
  }, [settings]);

  useEffect(() => {
    fetchNotifications();
    fetchSettings();
  }, [fetchNotifications, fetchSettings]);

  return {
    notifications,
    unreadCount,
    settings,
    isLoading,
    fetchNotifications,
    markAsRead,
    updateSettings,
  };
}