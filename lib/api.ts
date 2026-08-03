const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8007";

interface ApiResponse<T> {
  success?: boolean;
  error?: string;
  detail?: string;
  data?: T;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: any;
}

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

interface Memory {
  id: string;
  date: string;
  time?: string;
  content: string;
  summary?: string;
  tags: string[];
  topics?: string[];
  tasks?: string[];
  people?: string[];
  sentiment?: string;
}

interface SearchResult {
  id: string;
  date: string;
  similarity: number;
  content: string;
  tags: string[];
  summary?: string;
  sentiment?: string;
}

interface UploadResponse {
  success: boolean;
  memory_id?: string;
  database_id?: string;
  transcript?: string;
  extracted?: any;
  proposed_actions?: any[];
  action_count?: number;
  error?: string;
}

interface ProposedAction {
  id: string;
  title: string;
  description?: string;
  action_type: string;
  priority: string;
  status: string;
  confidence: number;
  memory_id?: string;
  related_entities?: string[];
  scheduled_time?: string;
  created_at: string;
}

interface ActionCounts {
  pending: number;
  approved: number;
  rejected: number;
  completed: number;
}

interface ActionQueueResponse {
  actions: ProposedAction[];
  counts: ActionCounts;
}

interface DashboardSummary {
  metrics: {
    total_memories: number;
    recent_memories_count: number;
    pending_actions: number;
    approved_actions: number;
    completed_actions: number;
    rejected_actions: number;
    google_connected: boolean;
    google_email?: string;
  };
  sentiment_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  top_tags: [string, number][];
  recent_memories: Array<{
    id: string;
    date: string;
    summary?: string;
    tags: string[];
    sentiment?: string;
    source?: string;
  }>;
  total_tags: number;
  unique_tags: number;
}

interface PrivacyExportResponse {
  export_date: string;
  user_id: string;
  user_email: string;
  data: {
    memories: any[];
    proposed_actions: any[];
    audit_logs: any[];
    google_credentials: any;
  };
  statistics: {
    total_memories: number;
    total_actions: number;
    total_audit_logs: number;
    google_connected: boolean;
  };
}

interface PrivacyClearResponse {
  success: boolean;
  message: string;
  details: {
    memories_deleted: number;
    actions_deleted: number;
    audit_logs_deleted: number;
    google_credentials_deleted: boolean;
  };
}

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  description: string;
  details: any;
  success: boolean;
  error_message?: string;
  created_at: string;
}

interface DailyBriefing {
  date: string;
  memories: {
    today_count: number;
    recent: Array<{
      id: string;
      summary?: string;
      tags: string[];
      sentiment?: string;
    }>;
  };
  actions: {
    pending_count: number;
    high_priority: Array<{
      id: string;
      title: string;
      priority: string;
      action_type: string;
    }>;
  };
  calendar: {
    today_events_count: number;
    upcoming: Array<{
      id: string;
      summary: string;
      start: string;
      end: string;
      location?: string;
    }>;
  };
  gmail: {
    important_messages_count: number;
    messages: Array<{
      id: string;
      subject: string;
      from: string;
      snippet: string;
    }>;
  };
  quick_stats: {
    total_memories: number;
    total_pending_actions: number;
  };
}

interface GoogleAuthStatus {
  connected: boolean;
  email?: string;
  scopes?: string[];
}

interface PoolsideHealth {
  poolside_available: boolean;
  openai_available: boolean;
  poolside_error?: string | null;
  openai_error?: string | null;
}

interface UserSettings {
  email_notifications: boolean;
  auto_create_events: boolean;
  theme: string;
  google_calendar_enabled: boolean;
  gmail_enabled: boolean;
}

/**
 * LifeLog API Client
 * Handles all API requests to the backend
 */
export class LifeLogApi {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Load tokens from localStorage if available
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  /**
   * Set authentication tokens
   */
  setTokens(tokens: { access_token: string; refresh_token: string }) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
    }
  }

  /**
   * Clear authentication tokens
   */
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  /**
   * Get default headers with auth token
   */
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = errorData.error || errorData.detail || "Unknown error";
      throw new Error(error);
    }

    const data = await response.json();
    return data as T;
  }

  /**
   * Make authenticated request
   */
  private async request<T>(
    method: string,
    endpoint: string,
    body?: any,
    isFormData: boolean = false,
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = isFormData ? {} : this.getHeaders();

    let response: Response;

    try {
      if (method === "GET") {
        response = await fetch(url, {
          method,
          headers,
          credentials: "include",
        });
      } else if (isFormData) {
        response = await fetch(url, {
          method,
          body,
          credentials: "include",
        });
      } else {
        response = await fetch(url, {
          method,
          headers,
          body: JSON.stringify(body),
          credentials: "include",
        });
      }

      // Check for 401 and try to refresh token
      if (response.status === 401 && this.refreshToken) {
        try {
          await this.refreshAccessToken();
          // Retry the request
          return this.request<T>(method, endpoint, body, isFormData);
        } catch (refreshError) {
          this.clearTokens();
          throw new Error("Session expired. Please login again.");
        }
      }

      return this.handleResponse<T>(response);
    } catch (error) {
      throw error;
    }
  }

  // ============================================================================
  // Authentication
  // ============================================================================

  /**
   * Register a new user
   */
  async register(
    email: string,
    username: string,
    password: string,
    full_name?: string,
  ): Promise<User> {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password, full_name }),
    });
    return this.handleResponse<User>(response);
  }

  /**
   * Login and get tokens
   */
  async login(email: string, password: string): Promise<AuthTokens> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const tokens = await this.handleResponse<AuthTokens>(response);
    this.setTokens(tokens);
    return tokens;
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>("GET", "/auth/me");
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.refreshToken}`,
      },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    const tokens = await this.handleResponse<AuthTokens>(response);
    this.setTokens(tokens);
  }

  // ============================================================================
  // Google OAuth
  // ============================================================================

  /**
   * Get Google OAuth authorization URL
   */
  getGoogleAuthUrl(scopes: string[] = []): string {
    const scopeParam =
      scopes.length > 0 ? `&scope=${scopes.join("&scope=")}` : "";
    return `${this.baseUrl}/auth/google?${scopeParam}`;
  }

  /**
   * Exchange Google OAuth code for tokens (callback step)
   */
  async exchangeGoogleCode(
    code: string,
    state: string,
  ): Promise<{
    success: boolean;
    message: string;
    email?: string;
    error?: string;
  }> {
    return this.request<{
      success: boolean;
      message: string;
      email?: string;
      error?: string;
    }>("GET", `/auth/google/callback?code=${code}&state=${state}`);
  }

  /**
   * Connect Google credentials (after OAuth callback)
   */
  async connectGoogle(
    access_token: string,
    refresh_token?: string,
    google_user_id?: string,
    email?: string,
    scopes?: string[],
  ): Promise<{ success: boolean; message: string; email?: string }> {
    return this.request<{ success: boolean; message: string; email?: string }>(
      "POST",
      "/auth/google/connect",
      { access_token, refresh_token, google_user_id, email, scopes },
    );
  }

  /**
   * Check Google connection status
   */
  async getGoogleStatus(): Promise<GoogleAuthStatus> {
    return this.request<GoogleAuthStatus>("GET", "/auth/google/status");
  }

  /**
   * Disconnect Google account
   */
  async disconnectGoogle(): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      "POST",
      "/auth/google/disconnect",
    );
  }

  // ============================================================================
  // Memories
  // ============================================================================

  /**
   * Upload audio file
   */
  async uploadAudio(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.detail || "Upload failed");
    }

    return response.json();
  }

  /**
   * Get list of memories
   */
  async getMemories(
    limit: number = 10,
    offset: number = 0,
  ): Promise<{ memories: Memory[] }> {
    return this.request<{ memories: Memory[] }>(
      "GET",
      `/api/memories?limit=${limit}&offset=${offset}`,
    );
  }

  /**
   * Get a specific memory
   */
  async getMemory(memoryId: string): Promise<Memory> {
    return this.request<Memory>("GET", `/api/memories/${memoryId}`);
  }

  /**
   * Delete a memory
   */
  async deleteMemory(memoryId: string): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(
      "DELETE",
      `/api/memories/${memoryId}`,
    );
  }

  // ============================================================================
  // Search
  // ============================================================================

  /**
   * Search memories
   */
  async searchMemories(
    query: string,
    threshold: number = 0.5,
  ): Promise<{ results: SearchResult[] }> {
    const params = new URLSearchParams({ query, threshold: String(threshold) });
    return this.request<{ results: SearchResult[] }>(
      "POST",
      `/api/search?${params.toString()}`,
    );
  }

  /**
   * Chat with Neural Core (LLM-grounded answer over memories)
   */
  async chat(
    question: string,
  ): Promise<{ answer: string; sources?: SearchResult[] }> {
    return this.request<{ answer: string; sources?: SearchResult[] }>(
      "POST",
      "/api/chat",
      { question },
    );
  }

  // ============================================================================
  // Settings
  // ============================================================================

  /**
   * Get user settings
   */
  async getSettings(): Promise<UserSettings> {
    return this.request<UserSettings>("GET", "/api/settings");
  }

  /**
   * Update user settings
   */
  async updateSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
    return this.request<UserSettings>("PUT", "/api/settings", settings);
  }

  // ============================================================================
  // Google Calendar
  // ============================================================================

  /**
   * List calendars
   */
  async listCalendars(): Promise<{ calendars: any[] }> {
    // This would call a new endpoint we need to add
    return this.request<{ calendars: any[] }>("GET", "/api/google/calendars");
  }

  /**
   * List events
   */
  async listEvents(calendarId: string = "primary"): Promise<{ events: any[] }> {
    return this.request<{ events: any[] }>(
      "GET",
      `/api/google/events?calendar_id=${calendarId}`,
    );
  }

  /**
   * Get free/busy slots
   */
  async getFreeBusy(
    timeMin?: string,
    timeMax?: string,
  ): Promise<{ freebusy: any }> {
    const params = new URLSearchParams();
    if (timeMin) params.set("time_min", timeMin);
    if (timeMax) params.set("time_max", timeMax);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request<{ freebusy: any }>("GET", `/api/google/freebusy${qs}`);
  }

  // ============================================================================
  // Google Gmail
  // ============================================================================

  /**
   * List messages
   */
  async listMessages(
    query?: string,
    maxResults: number = 10,
  ): Promise<{ messages: any[] }> {
    return this.request<{ messages: any[] }>(
      "GET",
      `/api/google/messages?query=${query || ""}&max_results=${maxResults}`,
    );
  }

  /**
   * List important unread messages
   */
  async listImportantMessages(
    maxResults: number = 10,
  ): Promise<{ messages: any[] }> {
    return this.request<{ messages: any[] }>(
      "GET",
      `/api/google/messages/important?max_results=${maxResults}`,
    );
  }

  // ============================================================================
  // Proposed Actions
  // ============================================================================

  /**
   * Get proposed actions with optional filters
   */
  async getActions(
    status?: string,
    action_type?: string,
    priority?: string,
    limit: number = 20,
    offset: number = 0,
  ): Promise<{ actions: ProposedAction[] }> {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (action_type) params.set("action_type", action_type);
    if (priority) params.set("priority", priority);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request<{ actions: ProposedAction[] }>(
      "GET",
      `/api/actions${qs}`,
    );
  }

  /**
   * Get pending actions (approval queue)
   */
  async getPendingActions(
    limit: number = 20,
  ): Promise<{ actions: ProposedAction[] }> {
    return this.request<{ actions: ProposedAction[] }>(
      "GET",
      `/api/actions/pending?limit=${limit}`,
    );
  }

  /**
   * Get action approval queue
   */
  async getApprovalQueue(limit: number = 20): Promise<ActionQueueResponse> {
    const actionsRes = await this.getPendingActions(limit);
    const countsRes = await this.getActionCounts();
    return {
      actions: actionsRes.actions,
      counts: countsRes.counts,
    };
  }

  /**
   * Get action counts by status
   */
  async getActionCounts(): Promise<{ counts: ActionCounts }> {
    return this.request<{ counts: ActionCounts }>("GET", "/api/actions/counts");
  }

  /**
   * Get a specific action
   */
  async getAction(actionId: string): Promise<ProposedAction> {
    return this.request<ProposedAction>("GET", `/api/actions/${actionId}`);
  }

  /**
   * Create a new proposed action
   */
  async createAction(actionData: {
    title: string;
    description?: string;
    action_type: string;
    priority?: string;
    confidence?: number;
    memory_id?: string;
    related_entities?: string[];
    scheduled_time?: string;
    location?: string;
    recipients?: string[];
  }): Promise<ProposedAction> {
    return this.request<ProposedAction>("POST", "/api/actions", actionData);
  }

  /**
   * Update an action
   */
  async updateAction(
    actionId: string,
    updates: {
      title?: string;
      description?: string;
      status?: string;
      priority?: string;
      scheduled_time?: string;
      location?: string;
      recipients?: string[];
    },
  ): Promise<ProposedAction> {
    return this.request<ProposedAction>(
      "PUT",
      `/api/actions/${actionId}`,
      updates,
    );
  }

  /**
   * Approve an action
   */
  async approveAction(
    actionId: string,
    scheduledTime?: string,
  ): Promise<ProposedAction> {
    return this.request<ProposedAction>(
      "POST",
      `/api/actions/${actionId}/approve`,
      {
        approve: true,
        scheduled_time: scheduledTime,
      },
    );
  }

  /**
   * Reject an action
   */
  async rejectAction(
    actionId: string,
    reason?: string,
  ): Promise<ProposedAction> {
    return this.request<ProposedAction>(
      "POST",
      `/api/actions/${actionId}/reject`,
      {
        approve: false,
        rejection_reason: reason,
      },
    );
  }

  /**
   * Mark an action as completed
   */
  async completeAction(
    actionId: string,
    notes?: string,
  ): Promise<ProposedAction> {
    return this.request<ProposedAction>(
      "POST",
      `/api/actions/${actionId}/complete`,
      {
        notes,
      },
    );
  }

  /**
   * Delete an action
   */
  async deleteAction(
    actionId: string,
  ): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      "DELETE",
      `/api/actions/${actionId}`,
    );
  }

  // ============================================================================
  // Dashboard
  // ============================================================================

  /**
   * Get dashboard summary
   */
  async getDashboardSummary(): Promise<DashboardSummary> {
    return this.request<DashboardSummary>("GET", "/api/dashboard/summary");
  }

  /**
   * Get daily briefing
   */
  async getDailyBriefing(): Promise<DailyBriefing> {
    return this.request<DailyBriefing>("GET", "/api/dashboard/daily-briefing");
  }

  // ============================================================================
  // MCP Tools
  // ============================================================================

  /**
   * List all MCP tools
   */
  async listMCPTools(): Promise<{ tools: any[]; count: number }> {
    return this.request<{ tools: any[]; count: number }>(
      "POST",
      "/api/mcp/tools",
    );
  }

  /**
   * Call an MCP tool
   */
  async callMCPTool(
    serverName: string,
    toolName: string,
    args: any,
  ): Promise<any> {
    return this.request<any>(
      "POST",
      `/api/mcp/tools/${serverName}/${toolName}`,
      args,
    );
  }

  /**
   * Check MCP servers health
   */
  async checkMCPHealth(): Promise<{ mcp_servers: any }> {
    return this.request<{ mcp_servers: any }>("GET", "/api/mcp/health");
  }

  // ============================================================================
  // Privacy Controls
  // ============================================================================

  /**
   * Export all user data
   */
  async exportUserData(): Promise<PrivacyExportResponse> {
    return this.request<PrivacyExportResponse>(
      "GET",
      "/api/privacy/export-data",
    );
  }

  /**
   * Clear all user data
   */
  async clearUserData(): Promise<PrivacyClearResponse> {
    return this.request<PrivacyClearResponse>(
      "POST",
      "/api/privacy/clear-data",
    );
  }

  /**
   * Revoke Google OAuth access
   */
  async revokeGoogleAccess(): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      "POST",
      "/api/privacy/revoke-google",
    );
  }

  // ============================================================================
  // Audit Logs
  // ============================================================================

  /**
   * Get audit logs for current user
   */
  async getAuditLogs(
    action?: string,
    entityType?: string,
    entityId?: string,
    limit: number = 50,
    offset: number = 0,
  ): Promise<{ audit_logs: AuditLog[] }> {
    const params = new URLSearchParams();
    if (action) params.set("action", action);
    if (entityType) params.set("entity_type", entityType);
    if (entityId) params.set("entity_id", entityId);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request<{ audit_logs: AuditLog[] }>(
      "GET",
      `/api/audit/logs${qs}`,
    );
  }

  /**
   * Get audit statistics
   */
  async getAuditStats(): Promise<any> {
    return this.request<any>("GET", "/api/audit/stats");
  }

  /**
   * Delete all audit logs for current user
   */
  async deleteUserAuditLogs(): Promise<{
    success: boolean;
    message: string;
    deleted_count: number;
  }> {
    return this.request<{
      success: boolean;
      message: string;
      deleted_count: number;
    }>("DELETE", "/api/audit/logs");
  }

  // ============================================================================
  // Poolside AI
  // ============================================================================

  /**
   * Check Poolside AI service health
   */
  async checkPoolsideHealth(): Promise<PoolsideHealth> {
    return this.request<PoolsideHealth>("GET", "/api/poolside/health");
  }
}

// Singleton instance
export const api = new LifeLogApi();

export default api;
