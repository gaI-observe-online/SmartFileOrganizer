/**
 * API client for SmartFileOrganizer backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface HealthStatus {
  status: string;
  database: string;
  ai_provider: string;
  disk_space_gb: number;
  memory_usage_percent: number;
}

export interface AIStatus {
  ai_connected: boolean;
  ai_endpoint: string;
  ai_model: string;
  database_path: string;
}

export interface ScanRequest {
  path: string;
  recursive?: boolean;
  auto_approve_threshold?: number;
}

export interface ScanResponse {
  scan_id: string;
  status: string;
  message: string;
}

export interface ScanProgress {
  scan_id: string;
  status: 'running' | 'paused' | 'completed' | 'cancelled' | 'error';
  total_files: number;
  processed_files: number;
  current_file: string | null;
  progress_percent: number;
  estimated_time_remaining: number | null;
}

export interface FileInfo {
  path: string;
  name: string;
  size: number;
  category: string;
  risk_score: number;
  risk_level: string;
  confidence: number;
}

export interface CategoryStats {
  category: string;
  count: number;
  total_size: number;
}

export interface Settings {
  ai_endpoint: string;
  ai_model: string;
  database_path: string;
  auto_approve_threshold: number;
  port: number;
  help_base_url: string;
}

export interface SettingsUpdate {
  ai_endpoint?: string;
  ai_model?: string;
  auto_approve_threshold?: number;
  help_base_url?: string;
}

export interface ScanListItem {
  id: string;
  timestamp: string;
  path: string;
  file_count: number;
}

// Health endpoints
export const getHealth = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/health');
  return response.data;
};

export const getStatus = async (): Promise<AIStatus> => {
  const response = await apiClient.get<AIStatus>('/status');
  return response.data;
};

// Scan endpoints
export const startScan = async (request: ScanRequest): Promise<ScanResponse> => {
  const response = await apiClient.post<ScanResponse>('/scan/start', request);
  return response.data;
};

export const getScanProgress = async (scanId: string): Promise<ScanProgress> => {
  const response = await apiClient.get<ScanProgress>(`/scan/${scanId}`);
  return response.data;
};

export const pauseScan = async (scanId: string): Promise<ScanResponse> => {
  const response = await apiClient.post<ScanResponse>(`/scan/${scanId}/pause`);
  return response.data;
};

export const cancelScan = async (scanId: string): Promise<ScanResponse> => {
  const response = await apiClient.post<ScanResponse>(`/scan/${scanId}/cancel`);
  return response.data;
};

export const listScans = async (limit: number = 50): Promise<ScanListItem[]> => {
  const response = await apiClient.get<ScanListItem[]>('/scans', { params: { limit } });
  return response.data;
};

// File endpoints
export const listFiles = async (
  category?: string,
  riskLevel?: string,
  limit: number = 100,
  offset: number = 0
): Promise<FileInfo[]> => {
  const response = await apiClient.get<FileInfo[]>('/files', {
    params: { category, risk_level: riskLevel, limit, offset },
  });
  return response.data;
};

export const getCategories = async (): Promise<CategoryStats[]> => {
  const response = await apiClient.get<CategoryStats[]>('/categories');
  return response.data;
};

// Settings endpoints
export const getSettings = async (): Promise<Settings> => {
  const response = await apiClient.get<Settings>('/settings');
  return response.data;
};

export const updateSettings = async (settings: SettingsUpdate): Promise<Settings> => {
  const response = await apiClient.put<Settings>('/settings', settings);
  return response.data;
};

// WebSocket connection for real-time updates
export const connectToScanUpdates = (
  scanId: string,
  onMessage: (data: any) => void,
  onError?: (error: any) => void
): WebSocket => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/scan/${scanId}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    onMessage(message);
  };

  ws.onerror = (error) => {
    if (onError) onError(error);
  };

  return ws;
};

export default apiClient;
