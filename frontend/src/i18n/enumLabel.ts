import type { TFunction } from './types';

const toCamelCase = (value: string): string => value.replace(/_([a-z])/g, (_, ch: string) => ch.toUpperCase());

/**
 * Translates an enum value coming from the API into a catalog label.
 *
 * API enums are `snake_case` (`in_progress`, `on_hold`) while catalog keys are
 * `camelCase` (`inProgress`, `onHold`), so the value is normalized before the
 * lookup. When a value has no catalog entry the raw value is returned, which
 * keeps an unmapped enum visible instead of rendering a dotted key.
 *
 * @example enumLabel(t, 'work.states', 'in_progress') // 'En curso'
 */
export function enumLabel(t: TFunction, group: string, value: string): string {
  const key = `${group}.${toCamelCase(value)}`;
  const translated = t(key);
  return translated === key ? value : translated;
}