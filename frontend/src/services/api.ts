import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token if available
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/auth';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async initiateLogin() {
    const response = await this.client.get('/auth/login');
    return response.data;
  }

  async completeLogin(deviceCode: string) {
    const response = await this.client.post('/auth/callback', { device_code: deviceCode });
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }
    }
    return response.data;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    const response = await this.client.post('/auth/refresh', { refresh_token: refreshToken });
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Emails
  async getEmails(params?: {
    account_id?: string;
    thread_id?: string;
    is_processed?: boolean;
    is_read?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.client.get('/emails', { params });
    return response.data;
  }

  async getEmail(emailId: string) {
    const response = await this.client.get(`/emails/${emailId}`);
    return response.data;
  }

  async searchEmails(query: string, limit = 10, sinceDays?: number) {
    const response = await this.client.post('/emails/search', { query, limit, since_days: sinceDays });
    return response.data;
  }

  async processEmail(emailId: string) {
    const response = await this.client.post(`/emails/${emailId}/process`);
    return response.data;
  }

  async getThreads(params?: { account_id?: string; limit?: number; offset?: number }) {
    const response = await this.client.get('/emails/threads', { params });
    return response.data;
  }

  // Tasks
  async getTasks(params?: {
    status?: string[];
    project_id?: string;
    priority?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.client.get('/tasks', { params });
    return response.data;
  }

  async getTaskStats() {
    const response = await this.client.get('/tasks/stats');
    return response.data;
  }

  async getTask(taskId: string) {
    const response = await this.client.get(`/tasks/${taskId}`);
    return response.data;
  }

  async createTask(data: {
    title: string;
    description?: string;
    priority?: string;
    estimated_minutes?: number;
    deadline_at?: string;
    project_id?: string;
    source_email_id?: string;
    metadata_json?: string;
  }) {
    const response = await this.client.post('/tasks', data);
    return response.data;
  }

  async updateTask(taskId: string, data: Record<string, unknown>) {
    const response = await this.client.patch(`/tasks/${taskId}`, data);
    return response.data;
  }

  async completeTask(taskId: string, actualMinutes?: number) {
    const response = await this.client.post(`/tasks/${taskId}/complete`, { actual_minutes: actualMinutes });
    return response.data;
  }

  async startTask(taskId: string) {
    const response = await this.client.post(`/tasks/${taskId}/start`);
    return response.data;
  }

  async blockTask(taskId: string) {
    const response = await this.client.post(`/tasks/${taskId}/block`);
    return response.data;
  }

  async unblockTask(taskId: string) {
    const response = await this.client.post(`/tasks/${taskId}/unblock`);
    return response.data;
  }

  async recommendNextTask(availableMinutes?: number) {
    const response = await this.client.post('/tasks/recommend-next', { available_minutes: availableMinutes });
    return response.data;
  }

  // Projects
  async getProjects(params?: { status?: string; limit?: number; offset?: number }) {
    const response = await this.client.get('/projects', { params });
    return response.data;
  }

  async getProject(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}`);
    return response.data;
  }

  async createProject(data: { name: string; description?: string; color?: string }) {
    const response = await this.client.post('/projects', data);
    return response.data;
  }

  async updateProject(projectId: string, data: Record<string, unknown>) {
    const response = await this.client.patch(`/projects/${projectId}`, data);
    return response.data;
  }

  async getProjectProgress(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}/progress`);
    return response.data;
  }

  async deleteProject(projectId: string) {
    const response = await this.client.delete(`/projects/${projectId}`);
    return response.data;
  }

  // AI
  async analyzeEmail(emailId: string) {
    const response = await this.client.post('/ai/analyze-email', { email_id: emailId });
    return response.data;
  }

  async askAI(question: string, context?: Record<string, unknown>) {
    const response = await this.client.post('/ai/ask', { question, context });
    return response.data;
  }

  async getDailyBriefing() {
    const response = await this.client.post('/ai/daily-briefing', {});
    return response.data;
  }

  async getEndOfDay() {
    const response = await this.client.post('/ai/end-of-day', {});
    return response.data;
  }

  async whatAmIForgetting() {
    const response = await this.client.post('/ai/what-am-i-forgetting', {});
    return response.data;
  }

  // Notifications
  async getNotifications(params?: { is_read?: boolean; severity?: string; limit?: number; offset?: number }) {
    const response = await this.client.get('/notifications', { params });
    return response.data;
  }

  async markNotificationRead(notificationId: string) {
    const response = await this.client.post(`/notifications/${notificationId}/read`);
    return response.data;
  }

  async getNotificationSettings() {
    const response = await this.client.get('/notifications/settings');
    return response.data;
  }

  async updateNotificationSettings(settings: Record<string, unknown>) {
    const response = await this.client.patch('/notifications/settings', settings);
    return response.data;
  }

  // Followups
  async getFollowups(status?: string) {
    const response = await this.client.get('/followups', { params: { status } });
    return response.data;
  }

  async prepareFollowup(followupId: string) {
    const response = await this.client.post(`/followups/${followupId}/prepare`);
    return response.data;
  }

  async dismissFollowup(followupId: string) {
    const response = await this.client.post(`/followups/${followupId}/dismiss`);
    return response.data;
  }

  async detectFollowups() {
    const response = await this.client.post('/followups/detect');
    return response.data;
  }

  // Health
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async aiHealthCheck() {
    const response = await this.client.get('/health/ai');
    return response.data;
  }
}

export const api = new ApiService();