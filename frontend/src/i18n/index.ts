export { I18nProvider, useI18n, useTranslation, currentLocale } from './I18nProvider';
export type { I18nContextValue } from './types';

export {
  DEFAULT_LOCALE,
  SUPPORTED_LOCALES,
  resolveLocale,
  translate,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
  resolveTimeZone,
  getActiveLocale,
} from './i18n';
export type { SupportedLocale } from './i18n';

export { resolvePluralCase, formatCount } from './plural';
export type { PluralCategory, PluralCase } from './plural';

export {
  PRODUCT_NAME,
  PRODUCT_TAGLINE,
  MAIN_MENU,
  WORK_STATES,
  WORK_STATE_BY_CODE,
  AI_STATES,
  AI_STATE_BY_CODE,
  NON_COUNTABLE_LABELS,
  resolveWorkState,
  resolveAIState,
  isNonCountable,
} from './glossary';
export type { MainMenuItem, WorkState, AIState, NonCountableLabel } from './glossary';

export type { Catalog, MessageValue, PluralMessage, TranslateOptions } from './types';