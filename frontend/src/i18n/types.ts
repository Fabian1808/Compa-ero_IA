import type { SupportedLocale } from './i18n';
import type { PluralCase, PluralCategory } from './plural';

/**
 * A countable message. `forms` must always provide `other`, which is the
 * fallback for any count that has no dedicated grammatical form.
 */
export interface PluralMessage {
  category: PluralCategory;
  forms: Partial<Record<PluralCase, string>> & { other: string };
}

export type MessageValue = string | PluralMessage;

export interface Catalog {
  [key: string]: MessageValue | Catalog;
}

export type InterpolationValues = Record<string, string | number>;

/** Options accepted by {@link translate}. */
export interface TranslateOptions extends InterpolationValues {
  /** Forces a semantic category, overriding the catalog default. */
  category?: PluralCategory;
  /** Supplies the count used for pluralization and for `{count}` interpolation. */
  count?: number;
}

/**
 * Signature of the translation function.
 *
 * Lives here rather than in `I18nProvider` so that helpers and presentational
 * components can import the type without pulling in a JSX module.
 */
export type TFunction = (key: string, options?: TranslateOptions) => string;

/**
 * Context value for the i18n provider.
 * Exported here to avoid circular imports with I18nProvider.tsx.
 */
export interface I18nContextValue {
  locale: SupportedLocale;
  availableLocales: readonly SupportedLocale[];
  setLocale: (locale: SupportedLocale) => void;
  t: TFunction;
}
