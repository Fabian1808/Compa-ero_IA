export interface EmailSearchRequest {
  query: string;
  limit?: number;
  since_days?: number;
}

export interface EmailProcessRequest {
  email_id: string;
}