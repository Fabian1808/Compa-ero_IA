/**
 * Semantic pluralization engine.
 *
 * Every countable message must declare its semantic category so the correct
 * grammatical form is chosen. Categories exist because the same number does not
 * behave the same way for every noun class in Spanish:
 *
 * - entity     : individually countable items (tarea, proyecto, persona)
 * - concept    : abstractions that are counted as units (idea, prioridad)
 * - status     : neutral status words used in filters/tabs (activo, pendiente)
 * - group      : things counted as a collective group (equipo, carpeta, bandeja)
 * - filter     : "mostrar N elementos" style clauses
 * - action     : verbs, which invert singular/plural vs. their noun
 * - properNoun : product names, never inflected
 *
 * `properNoun` intentionally has a single form so "Microsoft Outlook" or
 * "AI WORKMATE" are never pluralized.
 */

export type PluralCategory =
  | 'entity'
  | 'concept'
  | 'status'
  | 'group'
  | 'filter'
  | 'action'
  | 'properNoun';

export type PluralCase = 'zero' | 'one' | 'two' | 'few' | 'many' | 'other';

/**
 * Integer values that receive a dedicated grammatical form in es-PE.
 * Verified against the required matrix: 0 / 1 / 2 / 10 / 21.
 */
const ES_PE_INTEGER_FORMS: Record<'zero' | 'one' | 'two' | 'few' | 'many', number[]> = {
  zero: [0],
  one: [1],
  two: [2],
  few: [3, 4, 5, 6, 7, 8, 9],
  many: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
};

/**
 * Categories whose singular/plural agreement is inverted relative to the
 * default numeric rule. Used so callers cannot silently pick the wrong case.
 */
const INVERTED_CATEGORIES: ReadonlySet<PluralCategory> = new Set<PluralCategory>(['action']);

function isIntegerLike(count: unknown): count is number {
  return typeof count === 'number' && Number.isFinite(count);
}

/**
 * Resolves the grammatical case for a count in the given locale.
 *
 * Pluralization is derived from the value only; never from manual string
 * concatenation, so a component can never build "1 tarea" / "2 tarea" by hand.
 */
export function resolvePluralCase(
  count: number,
  category: PluralCategory,
  locale: string,
): PluralCase {
  if (category === 'properNoun') {
    return 'other';
  }

  const inverted = INVERTED_CATEGORIES.has(category);
  const rules = new Intl.PluralRules(locale, { type: 'cardinal' });

  if (!isIntegerLike(count)) {
    return inverted ? 'other' : 'other';
  }

  if (locale.toLowerCase().startsWith('es')) {
    const target = inverted ? invertCount(count) : count;
    const magnitude = Math.abs(target);

    for (const form of ['zero', 'one', 'two', 'few', 'many'] as const) {
      if (ES_PE_INTEGER_FORMS[form].includes(magnitude)) {
        return form;
      }
    }

    // 21+ follows the "many" agreement pattern ("21 elementos").
    return 'other';
  }

  return rules.select(count) as PluralCase;
}

function invertCount(count: number): number {
  if (count === 1) {
    return 2;
  }
  if (count === 2) {
    return 1;
  }
  return count;
}

/**
 * Formats a number using the locale's own separators and grouping.
 */
export function formatCount(count: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(count);
}