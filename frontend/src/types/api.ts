export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: string;
  user_id: string;
  provider: string;
  provider_account_id: string;
  status: 'active' | 'expired' | 'error' | 'disconnected';
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Email {
  id: string;
  account_id: string;
  graph_id: string;
  thread_id: string | null;
  subject: string;
  body_preview: string | null;
  body_text: string | null;
  sender_email: string;
  sender_name: string | null;
  recipients_json: string;
  received_at: string;
  has_attachments: boolean;
  importance: 'low' | 'normal' | 'high';
  categories_json: string;
  is_read: boolean;
  is_processed: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailThread {
  id: string;
  account_id: string;
  graph_thread_id: string;
  subject: string;
  participants_json: string;
  last_message_at: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'pending' | 'in_progress' | 'blocked' | 'waiting_response' | 'requires_decision' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Task {
  id: string;
  user_id: string;
  account_id: string | null;
  source_email_id: string | null;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  confidence_score: number;
  estimated_minutes: number | null;
  actual_minutes: number | null;
  deadline_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  project_id: string | null;
  dependencies_json: string;
  metadata_json: string;
  created_at: string;
  updated_at: string;
  project?: Project | null;
}

export type ProjectStatus = 'active' | 'on_hold' | 'completed' | 'archived';

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  color: string;
  progress: number;
  status: ProjectStatus;
  detected_automatically: boolean;
  created_at: string;
  updated_at: string;
}

export interface Commitment {
  id: string;
  user_id: string;
  source_email_id: string | null;
  description: string;
  committed_at: string;
  due_date: string | null;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'expired';
  confidence_score: number;
  related_task_id: string | null;
  created_at: string;
  updated_at: string;
}

export type FollowUpStatus = 'pending' | 'reminder_sent' | 'draft_prepared' | 'sent' | 'completed' | 'dismissed';

export interface FollowUp {
  id: string;
  user_id: string;
  source_email_id: string | null;
  contact_email: string;
  contact_name: string | null;
  subject: string;
  sent_at: string;
  expected_reply_by: string | null;
  status: FollowUpStatus;
  reminder_at: string | null;
  draft_response: string | null;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: string;
  account_id: string;
  graph_id: string;
  subject: string;
  start_at: string;
  end_at: string;
  attendees_json: string;
  location: string | null;
  is_online: boolean;
  meeting_url: string | null;
  created_at: string;
  updated_at: string;
}

export type NotificationSeverity = 'info' | 'reminder' | 'important' | 'critical';
export type NotificationType = 
  | 'deadline_approaching'
  | 'meeting_approaching'
  | 'followup_due'
  | 'task_blocked'
  | 'new_task_detected'
  | 'commitment_due'
  | 'daily_briefing'
  | 'end_of_day'
  | 'sync_completed'
  | 'sync_failed';

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  is_read: boolean;
  created_at: string;
}

/** Mirrors the backend `NotificationSettings` schema. */
export interface NotificationSettings {
  enabled: boolean;
  focus_mode_silence_non_critical: boolean;
  daily_briefing_enabled: boolean;
  daily_briefing_hour: number;
  end_of_day_enabled: boolean;
  end_of_day_hour: number;
  deadline_reminder_minutes_before: number;
  meeting_reminder_minutes_before: number;
}