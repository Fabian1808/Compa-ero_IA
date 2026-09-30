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

  /**
   * Generic passthroughs.
   *
   * Several screens call endpoints that have no dedicated wrapper yet. These
   * return the full axios response so callers keep using `.data`, matching the
   * dedicated wrappers and avoiding a second axios instance that would skip the
   * auth interceptors.
   *
   * The generic defaults to `any` because these endpoints are not typed yet;
   * adding a concrete response type per endpoint belongs with the wrapper for
   * that endpoint, not here.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async get<T = any>(url: string, config?: Record<string, unknown>) {
    return this.client.get<T>(url, config);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async post<T = any>(url: string, data?: unknown, config?: Record<string, unknown>) {
    return this.client.post<T>(url, data, config);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async put<T = any>(url: string, data?: unknown, config?: Record<string, unknown>) {
    return this.client.put<T>(url, data, config);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async patch<T = any>(url: string, data?: unknown, config?: Record<string, unknown>) {
    return this.client.patch<T>(url, data, config);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async delete<T = any>(url: string, config?: Record<string, unknown>) {
    return this.client.delete<T>(url, config);
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

  // Search
  async search(query: string, limit = 10, sourceTypes?: string[]) {
    const response = await this.client.post('/search', { query, limit, source_types: sourceTypes });
    return response.data;
  }

  async getMemoryStats() {
    const response = await this.client.get('/search/stats');
    return response.data;
  }

  async reindexMemory() {
    const response = await this.client.post('/search/reindex', {});
    return response.data;
  }

  async clearMemory() {
    const response = await this.client.delete('/search/clear');
    return response.data;
  }

  // WorkMap
  async getWorkMap() {
    const response = await this.client.get('/workmap');
    return response.data;
  }

  async getWorkMapProjectProgress(projectId: string) {
    const response = await this.client.get(`/workmap/project/${projectId}/progress`);
    return response.data;
  }

  async getBottlenecks() {
    const response = await this.client.get('/workmap/bottlenecks');
    return response.data;
  }

  // Connectors
  async getConnectors() {
    const response = await this.client.get('/connectors');
    return response.data;
  }

  async getConnectorInfo(connectorType: string) {
    const response = await this.client.get(`/connectors/${connectorType}/info`);
    return response.data;
  }

  async getAccounts() {
    const response = await this.client.get('/connectors/accounts');
    return response.data;
  }

  async testConnector(accountId: string, connectorType: string) {
    const response = await this.client.post(`/connectors/accounts/${accountId}/test/${connectorType}`);
    return response.data;
  }

  async syncConnector(accountId: string, connectorType: string) {
    const response = await this.client.post(`/connectors/accounts/${accountId}/sync/${connectorType}`);
    return response.data;
  }

  async getConnectorItems(accountId: string, connectorType: string, query = '', limit = 50) {
    const response = await this.client.get(`/connectors/accounts/${accountId}/items/${connectorType}`, {
      params: { query, limit }
    });
    return response.data;
  }

  async setExternalConnectorConfig(connectorType: string, config: Record<string, any>) {
    const response = await this.client.post('/connectors/external/config', { connector_type: connectorType, config });
    return response.data;
  }

  async getExternalConnectorConfig(connectorType: string) {
    const response = await this.client.get(`/connectors/external/config/${connectorType}`);
    return response.data;
  }

  // Admin
  async getTenants(params?: { page?: number; per_page?: number; search?: string; status?: string }) {
    const response = await this.client.get('/admin/tenants', { params });
    return response.data;
  }

  async createTenant(data: { name: string; slug: string; domain?: string; subscription_tier?: string }) {
    const response = await this.client.post('/admin/tenants', data);
    return response.data;
  }

  async getTenant(tenantId: string) {
    const response = await this.client.get(`/admin/tenants/${tenantId}`);
    return response.data;
  }

  async updateTenant(tenantId: string, data: Partial<{ name: string; domain: string; is_active: boolean; subscription_tier: string; subscription_status: string }>) {
    const response = await this.client.patch(`/admin/tenants/${tenantId}`, data);
    return response.data;
  }

  async deleteTenant(tenantId: string) {
    const response = await this.client.delete(`/admin/tenants/${tenantId}`);
    return response.data;
  }

  async getTenantUsers(tenantId: string, params?: { page?: number; per_page?: number }) {
    const response = await this.client.get(`/admin/tenants/${tenantId}/users`, { params });
    return response.data;
  }

  async addTenantUser(tenantId: string, data: { email: string; role?: string }) {
    const response = await this.client.post(`/admin/tenants/${tenantId}/users`, data);
    return response.data;
  }

  async updateTenantUser(tenantId: string, userId: string, data: { role?: string; is_active?: boolean }) {
    const response = await this.client.patch(`/admin/tenants/${tenantId}/users/${userId}`, data);
    return response.data;
  }

  async removeTenantUser(tenantId: string, userId: string) {
    const response = await this.client.delete(`/admin/tenants/${tenantId}/users/${userId}`);
    return response.data;
  }

  async createInvitation(tenantId: string, data: { email: string; role?: string }) {
    const response = await this.client.post(`/admin/tenants/${tenantId}/invitations`, data);
    return response.data;
  }

  async getInvitations(tenantId: string) {
    const response = await this.client.get(`/admin/tenants/${tenantId}/invitations`);
    return response.data;
  }

  async getTenantSettings(tenantId: string) {
    const response = await this.client.get(`/admin/tenants/${tenantId}/settings`);
    return response.data;
  }

  async updateTenantSettings(tenantId: string, data: Record<string, any>) {
    const response = await this.client.patch(`/admin/tenants/${tenantId}/settings`, data);
    return response.data;
  }

  async getAuditLogs(params?: { tenant_id?: string; user_id?: string; action?: string; start_date?: string; end_date?: string; page?: number; per_page?: number }) {
    const response = await this.client.get('/admin/audit-logs', { params });
    return response.data;
  }

  async getSystemMetrics() {
    const response = await this.client.get('/admin/metrics');
    return response.data;
  }

  // Initialization
  async getInitStatus() {
    const response = await this.client.get('/init/status');
    return response.data;
  }

  async startInitialization() {
    const response = await this.client.post('/init/start', {});
    return response.data;
  }

  async cancelInitialization() {
    const response = await this.client.post('/init/cancel', {});
    return response.data;
  }

  async resetInitialization() {
    const response = await this.client.post('/init/reset', {});
    return response.data;
  }

  // Installer
  async getInstallerStatus() {
    const response = await this.client.get('/installer/status');
    return response.data;
  }

  async getInstallProgress() {
    const response = await this.client.get('/installer/progress');
    return response.data;
  }

  async checkDependencies() {
    const response = await this.client.post('/installer/check');
    return response.data;
  }

  async installDependencies(dependencies?: string[]) {
    const response = await this.client.post('/installer/install', { dependencies });
    return response.data;
  }

  async installOllama() {
    const response = await this.client.post('/installer/install/ollama');
    return response.data;
  }

  async installModel(modelName: string) {
    const response = await this.client.post(`/installer/install/model/${modelName}`);
    return response.data;
  }

  async initializeFirstRun() {
    const response = await this.client.post('/installer/initialize');
    return response.data;
  }

  async checkFirstRunNeeded() {
    const response = await this.client.get('/installer/first-run-needed');
    return response.data;
  }

  async markInitialized() {
    const response = await this.client.post('/installer/mark-initialized');
    return response.data;
  }
}

export const api = new ApiService();