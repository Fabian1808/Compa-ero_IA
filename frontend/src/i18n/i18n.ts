import type { Catalog, MessageValue, PluralMessage, TranslateOptions } from './types';
import {
  formatCount,
  resolvePluralCase,
  type PluralCase,
  type PluralCategory,
} from './plural';
import { esPE } from './locales/es-PE';
import { enUS } from './locales/en-US';

export const DEFAULT_LOCALE = 'es-PE';
export const SUPPORTED_LOCALES = ['es-PE', 'en-US'] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

const CATALOGS: Record<SupportedLocale, Catalog> = {
  'es-PE': esPE,
  'en-US': enUS,
};

/** Injected by the provider so components can re-render on locale change. */
let activeLocale: SupportedLocale = DEFAULT_LOCALE;

export function setActiveLocale(locale: SupportedLocale): void {
  activeLocale = locale;
}

export function getActiveLocale(): SupportedLocale {
  return activeLocale;
}

/**
 * Maps an arbitrary BCP-47 tag onto a supported locale.
 * Falls back to the default locale so the UI never renders raw locale codes.
 */
export function resolveLocale(tag: string | undefined | null): SupportedLocale {
  if (!tag) {
    return DEFAULT_LOCALE;
  }

  const normalized = tag.toLowerCase();
  const exact = SUPPORTED_LOCALES.find((locale) => locale.toLowerCase() === normalized);
  if (exact) {
    return exact;
  }

  const base = normalized.split('-')[0];
  const byBase = SUPPORTED_LOCALES.find((locale) => locale.toLowerCase().split('-')[0] === base);
  return byBase ?? DEFAULT_LOCALE;
}

/**
 * Walks a dotted key through nested catalogs.
 *
 * Only a catalog can be descended into: a string leaf or a plural message has
 * no message keys of its own, so returning `undefined` lets the caller fall
 * back to the requested locale and finally to the key.
 */
function lookup(catalog: Catalog, key: string): MessageValue | Catalog | undefined {
  let node: MessageValue | Catalog | undefined = catalog;

  for (const segment of key.split('.')) {
    if (node === undefined || typeof node === 'string' || isPluralMessage(node)) {
      return undefined;
    }
    node = node[segment];
  }

  return node;
}

function isPluralMessage(value: MessageValue | Catalog): value is PluralMessage {
  return (
    typeof value === 'object' &&
    value !== null &&
    'category' in value &&
    'forms' in value
  );
}

/**
 * Resolves the closest available message, walking the fallback chain so a key
 * missing from `en-US` is served from `es-PE` instead of rendering the raw key.
 */
function resolveMessage(key: string): { value: MessageValue | Catalog; locale: SupportedLocale } | undefined {
  for (const locale of localeChain(activeLocale)) {
    const found = lookup(CATALOGS[locale], key);
    if (found !== undefined) {
      return { value: found, locale };
    }
  }
  return undefined;
}

function localeChain(locale: SupportedLocale): SupportedLocale[] {
  const base = locale.split('-')[0];
  const chain: SupportedLocale[] = [locale];
  const sameBase = SUPPORTED_LOCALES.filter(
    (candidate) => candidate !== locale && candidate.split('-')[0] === base,
  );
  return [...chain, ...sameBase, DEFAULT_LOCALE];
}

function interpolate(template: string, options: TranslateOptions, locale: string): string {
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = options[name];
    if (value === undefined) {
      return match;
    }
    return name === 'count' && typeof value === 'number'
      ? formatCount(value, locale)
      : String(value);
  });
}

function selectForm(
  message: PluralMessage,
  count: number,
  locale: string,
  override?: PluralCategory,
): string {
  const category = override ?? message.category;
  const pluralCase = resolvePluralCase(count, category, locale);
  const forms = message.forms as Partial<Record<PluralCase, string>>;
  return forms[pluralCase] ?? forms.other;
}

/**
 * Translates a dotted key.
 *
 * String values are interpolated as-is. Plural entries must be called with a
 * `count`; the grammatical form and the localized number are derived here so no
 * component ever concatenates a number with a noun by hand.
 */
export function translate(key: string, options: TranslateOptions = {}): string {
  const resolved = resolveMessage(key);

  if (!resolved) {
    // Surfacing the key makes an incomplete catalog obvious in development
    // instead of hiding the gap behind an empty label.
    return key;
  }

  const { value, locale } = resolved;

  if (typeof value === 'string') {
    return interpolate(value, options, locale);
  }

  if (isPluralMessage(value)) {
    const count = options.count;
    if (typeof count !== 'number') {
      return interpolate(value.forms.other.replace(/\{count\}/g, '').trim(), options, locale);
    }
    const form = selectForm(value, count, locale, options.category);
    return interpolate(form, { ...options, count }, locale);
  }

  return key;
}

/**
 * Convenience helper for read-only locale data (dates, numbers, relative time).
 * All formatting comes from the runtime's `Intl` data, never from hand-written
 * date strings.
 */
export function formatDate(
  value: Date | number | string,
  options: Intl.DateTimeFormatOptions = { dateStyle: 'long' },
): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return new Intl.DateTimeFormat(activeLocale, options).format(date);
}

export function formatDateTime(value: Date | number | string): string {
  return formatDate(value, { dateStyle: 'long', timeStyle: 'short' });
}

export function formatNumber(value: number, options: Intl.NumberFormatOptions = {}): string {
  return new Intl.NumberFormat(activeLocale, options).format(value);
}

export function formatPercent(value: number, fractionDigits = 0): string {
  return new Intl.NumberFormat(activeLocale, {
    style: 'percent',
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

/**
 * Resolves the user's timezone so relative dates match their own clock rather
 * than the machine's build timezone.
 */
export function resolveTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  } catch {
    return 'UTC';
  }
}