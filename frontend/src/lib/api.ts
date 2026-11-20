import { SupportedLanguage } from './translations';

export interface DocumentPage {
  id: string;
  page_number: number;
  extracted_text: string;
  ocr_confidence: number | null;
  word_count: number;
  created_at: string;
}

export interface DocumentDetail {
  id: string;
  title: string;
  file_url: string | null;
  download_url: string;
  file_type: string;
  file_size: number;
  page_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string;
  detected_language: string;
  created_at: string;
  updated_at: string;
  pages: DocumentPage[];
  section_count?: number;
}

export interface DocumentListItem {
  id: string;
  title: string;
  download_url: string;
  file_type: string;
  file_size: number;
  page_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  detected_language: string;
  created_at: string;
  updated_at: string;
  total_words: number;
  section_count?: number;
}

export interface UserProfile {
  id: number;
  email: string;
  full_name?: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  preferred_language: SupportedLanguage;
  text_size: 'normal' | 'large' | 'xlarge';
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  access: string;
  refresh?: string;
  user: UserProfile;
}

export interface HealthResponse {
  status: string;
  service: string;
}

// In-memory access token storage (Security Rule 3)
let inMemoryAccessToken: string | null = null;
let onAuthFailureCallback: (() => void) | null = null;

export function setAccessToken(token: string | null) {
  inMemoryAccessToken = token;
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setOnAuthFailure(callback: () => void) {
  onAuthFailureCallback = callback;
}

// Helper to make authenticated requests with auto-refresh on 401
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});

  if (inMemoryAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${inMemoryAccessToken}`);
  }

  // Include cookies by default (for httpOnly SameSite refresh token)
  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: 'include',
  };

  let res = await fetch(url, fetchOptions);

  // If 401 received and not currently calling auth endpoints, try silent refresh once
  if (res.status === 401 && !url.includes('/api/auth/')) {
    try {
      const refreshed = await refreshAuthToken();
      if (refreshed && inMemoryAccessToken) {
        // Retry original request with new access token
        headers.set('Authorization', `Bearer ${inMemoryAccessToken}`);
        res = await fetch(url, { ...fetchOptions, headers });
      } else {
        if (onAuthFailureCallback) onAuthFailureCallback();
      }
    } catch {
      if (onAuthFailureCallback) onAuthFailureCallback();
    }
  }

  return res;
}

/* ================= Authentication API ================= */

export async function registerUser(data: {
  full_name?: string;
  email: string;
  password: string;
  confirm_password?: string;
  preferred_language?: string;
  text_size?: string;
}): Promise<AuthResponse> {
  const res = await fetch('/api/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.full_name?.[0] ||
      errorData.email?.[0] ||
      errorData.password?.[0] ||
      errorData.confirm_password?.[0] ||
      errorData.non_field_errors?.[0] ||
      errorData.detail ||
      `Registration failed (HTTP ${res.status})`;
    throw new Error(message);
  }

  const result: AuthResponse = await res.json();
  setAccessToken(result.access);
  if (result.refresh) {
    try {
      sessionStorage.setItem('law-mithra-refresh-token', result.refresh);
    } catch {}
  }
  return result;
}

export async function loginUser(data: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const res = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('Too many login attempts. Please wait a moment before trying again.');
    }
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.non_field_errors?.[0] ||
      errorData.email?.[0] ||
      errorData.password?.[0] ||
      errorData.detail ||
      'Invalid email or password.';
    throw new Error(message);
  }

  const result: AuthResponse = await res.json();
  setAccessToken(result.access);
  if (result.refresh) {
    try {
      sessionStorage.setItem('law-mithra-refresh-token', result.refresh);
    } catch {}
  }
  return result;
}

export async function refreshAuthToken(): Promise<string | null> {
  try {
    let storedRefresh: string | null = null;
    try {
      storedRefresh = sessionStorage.getItem('law-mithra-refresh-token');
    } catch {}

    const payload = storedRefresh ? { refresh: storedRefresh } : {};
    const res = await fetch('/api/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'include',
    });

    if (!res.ok) {
      setAccessToken(null);
      try {
        sessionStorage.removeItem('law-mithra-refresh-token');
      } catch {}
      return null;
    }

    const data = await res.json();
    if (data.access) {
      setAccessToken(data.access);
      if (data.refresh) {
        try {
          sessionStorage.setItem('law-mithra-refresh-token', data.refresh);
        } catch {}
      }
      return data.access;
    }
    return null;
  } catch {
    setAccessToken(null);
    return null;
  }
}

export async function logoutUser(): Promise<void> {
  try {
    let storedRefresh: string | null = null;
    try {
      storedRefresh = sessionStorage.getItem('law-mithra-refresh-token');
    } catch {}

    const payload = storedRefresh ? { refresh: storedRefresh } : {};
    await fetch('/api/auth/logout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'include',
    });
  } finally {
    setAccessToken(null);
    try {
      sessionStorage.removeItem('law-mithra-refresh-token');
    } catch {}
  }
}

export async function fetchUserProfile(): Promise<UserProfile> {
  const res = await apiFetch('/api/auth/me/');
  if (!res.ok) {
    throw new Error('Failed to fetch user profile');
  }
  return res.json();
}

export async function updateUserProfile(data: Partial<Pick<UserProfile, 'preferred_language' | 'text_size'>>): Promise<UserProfile> {
  const res = await apiFetch('/api/auth/me/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update preferences');
  }

  return res.json();
}

export async function changeUserPassword(data: { current_password: string; new_password: string }): Promise<void> {
  const res = await apiFetch('/api/auth/change-password/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.current_password?.[0] ||
      errorData.new_password?.[0] ||
      errorData.detail ||
      'Failed to change password.';
    throw new Error(message);
  }

  const result = await res.json().catch(() => ({}));
  if (result.access) {
    setAccessToken(result.access);
  }
  if (result.refresh) {
    try {
      sessionStorage.setItem('law-mithra-refresh-token', result.refresh);
    } catch {}
  }
}

export async function deleteUserAccount(password: string): Promise<void> {
  const res = await apiFetch('/api/auth/me/', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.password?.[0] ||
      errorData.detail ||
      'Failed to delete account. Please verify your password.';
    throw new Error(message);
  }

  setAccessToken(null);
}

/* ================= Document API ================= */

export async function checkApiHealth(): Promise<HealthResponse> {
  const res = await fetch('/api/health/');
  if (!res.ok) {
    throw new Error(`Health check returned status ${res.status}`);
  }
  return res.json();
}

export async function uploadDocument(file: File, title?: string): Promise<DocumentDetail> {
  const formData = new FormData();
  formData.append('file', file);
  if (title && title.trim()) {
    formData.append('title', title.trim());
  }

  const res = await apiFetch('/api/documents/upload/', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('Upload limit reached. Please wait before uploading more documents.');
    }
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.file?.[0] ||
      errorData.title?.[0] ||
      errorData.detail ||
      `Upload failed with HTTP ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}

export async function fetchDocuments(): Promise<DocumentListItem[]> {
  const res = await apiFetch('/api/documents/');
  if (!res.ok) {
    throw new Error(`Failed to load documents: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDocument(id: string): Promise<DocumentDetail> {
  const res = await apiFetch(`/api/documents/${id}/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch document: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await apiFetch(`/api/documents/${id}/`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete document: ${res.statusText}`);
  }
}

export async function reprocessDocument(id: string): Promise<void> {
  const res = await apiFetch(`/api/documents/${id}/reprocess/`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to trigger reprocessing: ${res.statusText}`);
  }
}

/* ================= Section Detection API ================= */

export interface DetectedSection {
  id: string;
  page_number: number;
  act_raw: string;
  act_key: string;
  section_number: string;
  sub_clause: string;
  matched_text: string;
  start_char: number;
  end_char: number;
  detection_method: 'rule' | 'manual';
  review_status: 'auto' | 'confirmed' | 'rejected';
  created_at: string;
  updated_at?: string;
}

export interface SectionGroup {
  act_key: string;
  count: number;
  sections: DetectedSection[];
}

export interface GroupedSectionsResponse {
  total_count: number;
  groups: SectionGroup[];
}

export async function fetchDocumentSections(docId: string): Promise<GroupedSectionsResponse> {
  const res = await apiFetch(`/api/documents/${docId}/sections/`);
  if (!res.ok) {
    throw new Error(`Failed to load detected sections: ${res.statusText}`);
  }
  return res.json();
}

export async function detectDocumentSections(docId: string): Promise<DetectedSection[]> {
  const res = await apiFetch(`/api/documents/${docId}/detect-sections/`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to run section detection: ${res.statusText}`);
  }
  return res.json();
}

export async function updateDocumentSection(
  docId: string,
  sectionId: string,
  data: { review_status?: string; act_key?: string; section_number?: string }
): Promise<DetectedSection> {
  const res = await apiFetch(`/api/documents/${docId}/sections/${sectionId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to update section: ${res.statusText}`);
  }
  return res.json();
}

export async function addManualSection(
  docId: string,
  data: {
    page_number: number;
    start_char: number;
    end_char: number;
    section_number: string;
    act_key?: string;
    sub_clause?: string;
  }
): Promise<DetectedSection> {
  const res = await apiFetch(`/api/documents/${docId}/sections/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to add manual section`);
  }
  return res.json();
}

export async function deleteManualSection(docId: string, sectionId: string): Promise<void> {
  const res = await apiFetch(`/api/documents/${docId}/sections/${sectionId}/`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete manual section`);
  }
}

export interface LegalAssistantResponse {
  detected_language: string;
  target_language: string;
  legal_issue: string;
  remedies: string[];
  applicable_sections: {
    act: string;
    sections: string[];
    summary: string;
    original_english_statute: string;
  }[];
  explanation?: string;
  advice?: string;
  statutory_references?: string[];
  disclaimer?: string;
}

// ─── Universal Complaint Analysis Report ───────────────────────────────────

export interface LegalProvision {
  act_section: string;
  relevance: string;
  caveat: string;
}

export interface ComplaintReport {
  id: string;
  report_id: string;
  generated_date: string;
  updated_at: string;
  document_title: string;
  case_complaint_no: string;
  status: string;
  case_status: string;
  complaint_type: string;
  parties_involved: string;
  incident_date_place: string;
  complaint_summary: string;
  legal_provisions: LegalProvision[];
  evidence_available: string[];
  evidence_missing: string[];
  complainant_side: string;
  respondent_side: string;
  persons_role: string;
  rights_next_steps: string;
  advocate_questions: string;
  current_stage: string;
  last_updated_date: string;
  version: number;
  error_message?: string;
}

export interface ReportListResponse {
  count: number;
  reports: ComplaintReport[];
}

/** POST – generate (or regenerate) a report; creates new versioned record */
export async function generateComplaintReport(
  documentId: string,
  language: string = 'en'
): Promise<ComplaintReport> {
  const res = await apiFetch(`/api/documents/${documentId}/generate-report/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Report generation failed (${res.status})`);
  }
  return res.json();
}

/** GET – fetch the latest completed report for a document */
export async function fetchLatestReport(documentId: string): Promise<ComplaintReport> {
  const res = await apiFetch(`/api/documents/${documentId}/reports/latest/`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `No report found (${res.status})`);
  }
  return res.json();
}

/** GET – list all report versions */
export async function fetchReportList(documentId: string): Promise<ReportListResponse> {
  const res = await apiFetch(`/api/documents/${documentId}/reports/`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch reports (${res.status})`);
  }
  return res.json();
}

/** Trigger authenticated PDF download via blob */
export async function downloadReportPDF(documentId: string, reportDbId: string): Promise<void> {
  const res = await apiFetch(`/api/documents/${documentId}/reports/${reportDbId}/pdf/`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.error || `Failed to download PDF (${res.status})`);
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = window.document.createElement('a');
  const disp = res.headers.get('Content-Disposition') || '';
  const match = disp.match(/filename="([^"]+)"/);
  a.download = match ? match[1] : 'LawMithra_Report.pdf';
  a.href = blobUrl;
  a.click();
  URL.revokeObjectURL(blobUrl);
}

/* ================= Chat & Conversation Session API ================= */

export interface ChatMessageItem {
  id: string;
  sequence_number: number;
  client_request_id?: string;
  sender: 'user' | 'assistant';
  content: string;
  statutory_citations?: any[];
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ChatSessionListItem {
  id: string;
  title: string;
  case_role: string;
  preferred_language: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSessionListItem {
  messages: ChatMessageItem[];
}

export async function fetchChatSessions(): Promise<ChatSessionListItem[]> {
  const res = await apiFetch('/api/knowledge/sessions/');
  if (!res.ok) {
    throw new Error('Failed to load conversation history');
  }
  return res.json();
}

export async function fetchChatSessionDetail(sessionId: string): Promise<ChatSessionDetail> {
  const res = await apiFetch(`/api/knowledge/sessions/${sessionId}/`);
  if (!res.ok) {
    throw new Error('Failed to load conversation thread');
  }
  return res.json();
}

export async function createChatSession(data: {
  title?: string;
  preferred_language?: string;
  case_role?: string;
} = {}): Promise<ChatSessionDetail> {
  const res = await apiFetch('/api/knowledge/sessions/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error('Failed to create new chat session');
  }
  return res.json();
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  const res = await apiFetch(`/api/knowledge/sessions/${sessionId}/`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Failed to delete chat session');
  }
}

export async function askLegalAssistant(
  query: string,
  preferredLanguage: string = 'en',
  autoDetect: boolean = true,
  sessionId?: string | null,
  clientRequestId?: string | null
): Promise<LegalAssistantResponse & {
  session_id?: string;
  session_title?: string;
  assistant_message_id?: string;
  user_message_id?: string;
}> {
  const payload: Record<string, any> = {
    query,
    preferred_language: preferredLanguage,
    auto_detect_language: autoDetect,
  };
  if (sessionId) payload.session_id = sessionId;
  if (clientRequestId) payload.client_request_id = clientRequestId;

  const res = await apiFetch('/api/knowledge/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Legal AI service error (${res.status})`);
  }

  const data = await res.json();
  const statutes = (data.applicable_sections || []).flatMap((s: any) =>
    (s.sections || []).map((sec: string) => `${sec} (${s.act})`)
  );

  return {
    ...data,
    explanation: data.legal_issue || data.explanation,
    statutory_references: statutes,
  };
}
