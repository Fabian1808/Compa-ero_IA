// System Tray Integration for AI Workmate
// Handles background operation, quick actions, and system tray menu

import { useEffect, useState } from 'react';
import { useTray, useWindow, useEventListener } from '@tauri-apps/api/window';
import { useTray as useTrayApi, TrayIcon } from '@tauri-apps/api/tray';
import { useNotification } from '@tauri-apps/api/notification';
import { useStore } from '@/store/uiStore';

interface TrayMenuItem {
  id: string;
  text: string;
  action: () => void;
  enabled?: boolean;
  checked?: boolean;
}

export function useSystemTray() {
  const [isMinimized, setIsMinimized] = useState(false);
  const { toggleSidebar } = useStore();

  useEffect(() => {
    // Register global shortcuts
    registerShortcuts();
    
    // Setup tray
    setupTray();
    
    // Handle window events
    handleWindowEvents();
    
    return () => {
      cleanup();
    };
  }, []);

  const registerShortcuts = async () => {
    try {
      const { registerGlobalShortcut } = await import('@tauri-apps/api/globalShortcut');
      
      // Ctrl+Shift+W: Show/hide window
      await registerGlobalShortcut('Ctrl+Shift+W', () => {
        toggleWindow();
      });
      
      // Ctrl+Shift+F: Focus mode
      await registerGlobalShortcut('Ctrl+Shift+F', () => {
        // Navigate to focus page
        window.location.href = '/focus';
        showWindow();
      });
      
      // Ctrl+Shift+S: Sync now
      await registerGlobalShortcut('Ctrl+Shift+S', () => {
        triggerSync();
      });
    } catch (err) {
      console.warn('Global shortcuts not available:', err);
    }
  };

  const setupTray = async () => {
    try {
      const { TrayIcon, TrayIconOptions } = await import('@tauri-apps/api/tray');
      const { appWindow } = await import('@tauri-apps/api/window');
      const { readFile } = await import('@tauri-apps/api/fs');
      const { join } = await import('@tauri-apps/api/path');
      
      // Load tray icon
      const iconPath = await join('icon.png');
      
      const trayOptions: TrayIconOptions = {
        iconPath,
        menu: [
          {
            id: 'show',
            text: 'Mostrar AI Workmate',
            action: () => showWindow(),
          },
          {
            id: 'focus',
            text: 'Modo Foco',
            action: () => {
              showWindow();
              // Navigate to focus - will be handled by router
            },
          },
          {
            id: 'sync',
            text: 'Sincronizar ahora',
            action: () => triggerSync(),
          },
          {
            type: 'separator',
          },
          {
            id: 'settings',
            text: 'Configuración',
            action: () => {
              showWindow();
              // Navigate to settings
            },
          },
          {
            type: 'separator',
          },
          {
            id: 'quit',
            text: 'Salir',
            action: () => {
              const { appWindow } = require('@tauri-apps/api/window');
              appWindow.close();
            },
          },
        ],
      };

      const tray = new TrayIcon(trayOptions);
      
      // Double click to show/hide
      tray.onDoubleClick(() => {
        toggleWindow();
      });

      // Store tray reference for cleanup
      (window as any).__tray = tray;
      
    } catch (err) {
      console.warn('System tray not available:', err);
    }
  };

  const handleWindowEvents = async () => {
    const { appWindow } = await import('@tauri-apps/api/window');
    
    // Prevent close, minimize to tray instead
    appWindow.onCloseRequested(async (event) => {
      event.preventDefault();
      hideWindow();
    });
    
    // Track minimize
    appWindow.onMinimized(() => {
      setIsMinimized(true);
      hideWindow();
    });
  };

  const showWindow = async () => {
    try {
      const { appWindow } = await import('@tauri-apps/api/window');
      await appWindow.show();
      await appWindow.setFocus();
      setIsMinimized(false);
    } catch (err) {
      console.error('Error showing window:', err);
    }
  };

  const hideWindow = async () => {
    try {
      const { appWindow } = await import('@tauri-apps/api/window');
      await appWindow.hide();
      setIsMinimized(true);
    } catch (err) {
      console.error('Error hiding window:', err);
    }
  };

  const toggleWindow = async () => {
    try {
      const { appWindow } = await import('@tauri-apps/api/window');
      const isVisible = await appWindow.isVisible();
      if (isVisible) {
        await hideWindow();
      } else {
        await showWindow();
      }
    } catch (err) {
      console.error('Error toggling window:', err);
    }
  };

  const triggerSync = async () => {
    try {
      // Trigger sync via API
      await fetch('/api/v1/sync', { method: 'POST' });
      
      // Show notification
      const { sendNotification } = await import('@tauri-apps/api/notification');
      await sendNotification({
        title: 'AI Workmate',
        body: 'Sincronización iniciada',
      });
    } catch (err) {
      console.error('Sync error:', err);
    }
  };

  const cleanup = async () => {
    try {
      const { unregisterGlobalShortcut } = await import('@tauri-apps/api/globalShortcut');
      await unregisterGlobalShortcut('Ctrl+Shift+W');
      await unregisterGlobalShortcut('Ctrl+Shift+F');
      await unregisterGlobalShortcut('Ctrl+Shift+S');
      
      const tray = (window as any).__tray;
      if (tray) {
        await tray.destroy();
      }
    } catch (err) {
      console.warn('Cleanup error:', err);
    }
  };

  return {
    isMinimized,
    showWindow,
    hideWindow,
    toggleWindow,
    triggerSync,
  };
}

// Notification helper
export async function showNotification(title: string, body: string, options?: {
  icon?: string;
  onClick?: () => void;
}) {
  try {
    const { sendNotification, NotificationPermission } = await import('@tauri-apps/api/notification');
    
    // Request permission if needed
    const permission = await NotificationPermission.request();
    if (permission !== 'granted') {
      console.warn('Notification permission not granted');
      return;
    }

    await sendNotification({
      title,
      body,
      icon: options?.icon,
    });
  } catch (err) {
    console.warn('Notification failed:', err);
  }
}

// Auto-start with Windows
export async function setAutoStart(enabled: boolean) {
  try {
    const { appWindow } = await import('@tauri-apps/api/window');
    if (enabled) {
      // This would require tauri-plugin-autostart
      console.log('Auto-start enabled');
    } else {
      console.log('Auto-start disabled');
    }
  } catch (err) {
    console.warn('Auto-start not available:', err);
  }
}

// Prevent sleep during sync
export async function preventSleep(prevent: boolean) {
  try {
    const { preventSleep } = await import('@tauri-apps/api/power');
    if (prevent) {
      await preventSleep();
    } else {
      // Allow sleep again - would need to track the handle
    }
  } catch (err) {
    console.warn('Power management not available:', err);
  }
}