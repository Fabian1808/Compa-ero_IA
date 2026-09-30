// Re-exports from api.ts for backward compatibility
export type { Task, TaskStatus } from './api';
import type { TaskStatus } from './api';

/** Matches the backend `Task.priority` enum. */
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export interface TaskFilter {
  status?: TaskStatus[];
  project_id?: string;
  priority?: string;
  search?: string;
}

export interface TaskRecommendation {
  recommended_task_id: string | null;
  title: string;
  reasoning: string;
  estimated_minutes: number | null;
  deadline_at: string | null;
  confidence: number;
  alternative_task_ids: string[];
}

export interface TaskStats {
  completed_today: number;
  pending: number;
  in_progress: number;
  blocked: number;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  estimated_minutes?: number;
  deadline_at?: string;
  project_id?: string;
  source_email_id?: string;
  metadata_json?: string;
}

export interface UpdateTaskData {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  estimated_minutes?: number;
  actual_minutes?: number;
  deadline_at?: string;
  project_id?: string;
  dependencies_json?: string;
  metadata_json?: string;
}
