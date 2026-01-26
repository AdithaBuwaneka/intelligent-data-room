// Message types for chat interface
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  plan?: string;
  chartConfig?: ChartConfig | null;
}

// Chart configuration for Recharts
export interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'area';
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string | string[];
  title?: string;
  colors?: string[];
}

// File upload response from backend
export interface FileUploadResponse {
  file_id: string;
  file_url: string;
  filename: string;
  columns: string[];
  row_count: number;
  session_id: string;
}

// Query request to backend
export interface QueryRequest {
  session_id: string;
  question: string;
  file_url: string;
}

// Query response from backend
export interface QueryResponse {
  answer: string;
  plan: string;
  chart_config: ChartConfig | null;
  execution_time?: number;
}

// File metadata stored in state
export interface FileMetadata {
  fileId: string;
  fileUrl: string;
  filename: string;
  columns: string[];
  rowCount: number;
}

// Chat session state
export interface ChatSession {
  sessionId: string;
  file: FileMetadata | null;
  messages: Message[];
  isLoading: boolean;
}

// API Error response
export interface ApiError {
  detail: string;
  status_code: number;
}
