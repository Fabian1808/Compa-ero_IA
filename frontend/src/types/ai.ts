export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface AskAIRequest {
  question: string;
  context?: Record<string, unknown>;
}

export interface AskAIResponse {
  answer: string;
  sources: Array<Record<string, unknown>>;
  tool_calls: Array<{
    tool: string;
    result: Record<string, unknown>;
  }>;
}

export interface AnalyzeEmailResponse {
  tasks_detected: number;
  commitments_detected: number;
  deadlines_detected: number;
  followups_detected: number;
  tasks?: Array<{
    title: string;
    description: string;
    deadline_iso: string | null;
    priority: string;
    estimated_minutes: number;
    project_hint: string | null;
    confidence: number;
    evidence_quote: string;
  }>;
  commitments?: Array<{
    description: string;
    due_date_iso: string | null;
    confidence: number;
    evidence_quote: string;
    is_user_commitment: boolean;
  }>;
  deadlines?: Array<{
    description: string;
    deadline_iso: string;
    confidence: number;
    evidence_quote: string;
    is_external: boolean;
  }>;
}