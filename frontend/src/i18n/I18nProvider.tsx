import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  DEFAULT_LOCALE,
  SUPPORTED_LOCALES,
  getActiveLocale,
  resolveLocale,
  setActiveLocale,
  translate,
  type SupportedLocale,
} from './i18n';
import type { PluralCategory } from './plural';

const STORAGE_KEY = 'aiworkmate.locale';

export type { TFunction } from './types';
import type { I18nContextValue } from './types';

const I18nContext = createContext<I18nContextValue | null>(null);

function detectInitialLocale(): SupportedLocale {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE;
  }

  const stored = window.localStorage?.getItem(STORAGE_KEY);
  if (stored) {
    return resolveLocale(stored);
  }

  const preferred = window.navigator?.languages ?? [window.navigator?.language];
  for (const tag of preferred) {
    const resolved = resolveLocale(tag);
    // Only honor a browser language that actually maps to a supported catalog.
    if (resolved === DEFAULT_LOCALE && !tag?.toLowerCase().startsWith('es')) {
      continue;
    }
    return resolved;
  }

  return DEFAULT_LOCALE;
}

/**
 * Provides the active locale and the translation function.
 *
 * Components read text exclusively through `t()` so no user-visible string is
 * hardcoded in the view layer.
 */
export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<SupportedLocale>(detectInitialLocale);

  useEffect(() => {
    setActiveLocale(locale);
  }, [locale]);

  const setLocale = useCallback((next: SupportedLocale) => {
    setLocaleState(next);
    setActiveLocale(next);
    try {
      window.localStorage?.setItem(STORAGE_KEY, next);
    } catch {
      // Storage may be unavailable in restricted profiles; the in-memory locale
      // still applies for this session.
    }
  }, []);

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      availableLocales: SUPPORTED_LOCALES,
      setLocale,
      t: (key, options) => translate(key, options ?? {}),
    }),
    [locale, setLocale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}

/**
 * Convenience hook for components that only need the translation function.
 */
export function useTranslation() {
  return useI18n();
}

/** Reads the locale without subscribing to changes. */
export function currentLocale(): SupportedLocale {
  return getActiveLocale();
}