import { useCallback, useEffect, useState } from 'react';
import { api } from '@/services/api';

export function useSync() {
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  const triggerSync = useCallback(async () => {
    setIsSyncing(true);
    setSyncError(null);
    try {
      // In a real app, this would call the sync endpoint
      // For now, just update the timestamp
      const now = new Date().toISOString();
      setLastSync(now);
      localStorage.setItem('last_sync', now);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('last_sync');
    if (saved) {
      setLastSync(saved);
    }
  }, []);

  return {
    lastSync,
    isSyncing,
    syncError,
    triggerSync,
  };
}