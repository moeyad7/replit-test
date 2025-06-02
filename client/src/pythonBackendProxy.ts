/**
 * Proxy module to redirect API calls to the Python backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export interface QueryResponse {
  agent_response: string;
  is_error?: boolean;
  error_type?: string;
  error_message?: string;
  sqlQuery?: string;
  data?: any;
  insights?: any;
}

export interface ChatMessage {
  timestamp: number;
  question: string;
  response: QueryResponse;
}

export interface ChatHistory {
  history: ChatMessage[];
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitQuery = async (question: string, sessionId?: string): Promise<QueryResponse> => {
  const response = await api.post('/query', { question, session_id: sessionId });
  return response.data;
};

export const getSchema = async () => {
  const response = await api.get('/schema');
  return response.data.schema;
};

// New chat session endpoints
export const createChatSession = async (): Promise<{ session_id: string }> => {
  const response = await api.post('/chat/session');
  return response.data;
};

export const getChatHistory = async (sessionId: string): Promise<ChatHistory> => {
  const response = await api.get(`/chat/history/${sessionId}`);
  return response.data;
};

export const clearChatHistory = async (sessionId: string): Promise<void> => {
  await api.delete(`/chat/history/${sessionId}`);
};