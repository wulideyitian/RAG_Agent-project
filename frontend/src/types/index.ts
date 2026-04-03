// API 响应类型定义
export interface ChatRequest {
  query: string;
  stream?: boolean;
  context?: any;
}

export interface ChatResponse {
    response: string;
  success: boolean;
  data: string;
  message?: string;
}

export interface StreamChatResponse {
  success: boolean;
  data: string;
  type: 'chunk' | 'done';
}

export interface HealthResponse {
  status: string;
  message: string;
}

export interface FileUploadResponse {
  success: boolean;
  data: {
    filename: string;
    path: string;
    size: number;
  };
  message: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
