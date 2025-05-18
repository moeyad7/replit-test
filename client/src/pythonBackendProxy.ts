/**
 * Proxy module to redirect API calls to the Python backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export interface QueryResponse {
  queryUnderstanding: string;
  sqlQuery: string;
  databaseResults: {
    count: number;
    time: number;
  };
  title: string;
  data: any[];
  insights: Array<{
    id: number;
    text: string;
  }>;
  recommendations: Array<{
    id: number;
    title: string;
    description: string;
    type: string;
  }>;
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