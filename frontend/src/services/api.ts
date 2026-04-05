import axios from 'axios';
import type { ChatRequest, ChatResponse, HealthResponse, FileUploadResponse } from '../types';

const API_BASE_URL = '/api';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 健康检查
 */
export const healthCheck = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

/**
 * 发送聊天请求（非流式）
 */
export const sendChatRequest = async (request: {
  messages: { role: "user" | "assistant"; content: string }[];
  stream: boolean;
  user_id: string;
  session_id: string;
  save_to_db: boolean
}): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/chat/', request);
  return response.data;
};

/**
 * 发送流式聊天请求
 * @param query - 用户问题
 * @param onChunk - 接收数据块的回调函数
 * @returns AbortController 用于取消请求
 */
export const sendStreamChatRequest = (
  query: string,
  onChunk: (data: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
): AbortController => {
  const controller = new AbortController();
  
  // 使用 fetch API 处理 SSE 流
  fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, stream: true }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // 解析 SSE 格式的数据
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留不完整的一行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              onComplete?.();
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.success && parsed.data) {
                onChunk(parsed.data);
              }
            } catch (e) {
              console.error('解析流数据失败:', e);
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name === 'AbortError') {
        console.log('流式请求被取消');
      } else {
        onError?.(error);
      }
    });

  return controller;
};

/**
 * 上传文件
 */
export const uploadFile = async (
  file: File,
  description?: string
): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (description) {
    formData.append('description', description);
  }

  const response = await apiClient.post<FileUploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};
