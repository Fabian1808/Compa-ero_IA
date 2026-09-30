/**
 * Canonical glossary for AI WORKMATE.
 *
 * This is the single source of truth for product-visible terminology. UI code
 * must never hardcode these words: they are referenced through the message
 * catalog so a terminology change lands in one place and is verifiable.
 *
 * Rules enforced here:
 * - Product name is always "AI WORKMATE" (uppercase, never localized).
 * - Technical internals (tokens, prompts, model names, API paths) are never
 *   shown to the user, so they have no entry.
 * - "Conexiones" is the user-facing word for connectors/integrations.
 * - Work states use "Completada" when referring to a task (feminine) and
 *   "Completado" only when the subject is not a task.
 */

export const PRODUCT_NAME = 'AI WORKMATE';
export const PRODUCT_TAGLINE = 'Compañero de trabajo inteligente';

/** Official main menu, in display order. */
export const MAIN_MENU = [
  'Inicio',
  'Mi trabajo',
  'Proyectos',
  'Personas',
  'Calendario',
  'Memoria',
  'Conexiones',
  'Configuración',
] as const;

export type MainMenuItem = (typeof MAIN_MENU)[number];

/** Official work states. */
export const WORK_STATES = [
  'Pendiente',
  'En curso',
  'Bloqueado',
  'Esperando respuesta',
  'Requiere decisión',
  'Completada',
] as const;

export type WorkState = (typeof WORK_STATES)[number];

/**
 * Maps backend enum values to the official display terms.
 * Unknown values are surfaced verbatim rather than silently dropped.
 */
export const WORK_STATE_BY_CODE: Record<string, WorkState> = {
  pending: 'Pendiente',
  in_progress: 'En curso',
  blocked: 'Bloqueado',
  waiting: 'Esperando respuesta',
  needs_decision: 'Requiere decisión',
  completed: 'Completada',
};

/** Official AI origin/permission states, ordered from weakest to strongest. */
export const AI_STATES = [
  'Detectado',
  'Inferido',
  'Sugerido',
  'Confirmado',
  'Ejecutado',
] as const;

export type AIState = (typeof AI_STATES)[number];

/**
 * Maps AI result codes to official display terms.
 * `executed` is only reachable after an explicit user confirmation.
 */
export const AI_STATE_BY_CODE: Record<string, AIState> = {
  detected: 'Detectado',
  inferred: 'Inferido',
  suggested: 'Sugerido',
  confirmed: 'Confirmado',
  executed: 'Ejecutado',
};

/** Terms that must never be pluralized by the pluralization engine. */
export const NON_COUNTABLE_LABELS = [
  'AI WORKMATE',
  'Microsoft Outlook',
  'Microsoft Teams',
  'Microsoft OneDrive',
  'Microsoft SharePoint',
  'Microsoft Excel',
  'Microsoft Power BI',
  'Outlook',
  'Equipos',
  'Energía',
  'Configuración',
  'Administración',
  'Capacitación',
] as const;

export type NonCountableLabel = (typeof NON_COUNTABLE_LABELS)[number];

/**
 * Resolves a backend work-state code to its official term.
 */
export function resolveWorkState(code: string): string {
  return WORK_STATE_BY_CODE[code] ?? code;
}

/**
 * Resolves a backend AI-state code to its official term.
 */
export function resolveAIState(code: string): string {
  return AI_STATE_BY_CODE[code] ?? code;
}

/**
 * True when a label must stay invariable regardless of the count.
 */
export function isNonCountable(label: string): boolean {
  return (NON_COUNTABLE_LABELS as readonly string[]).includes(label);
}