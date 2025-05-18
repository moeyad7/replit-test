import { useState, useEffect } from 'react';
import { createChatSession, getChatHistory, clearChatHistory, ChatMessage } from '../pythonBackendProxy';

export const useChatSession = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize chat session
  useEffect(() => {
    const initSession = async () => {
      try {
        const { session_id } = await createChatSession();
        setSessionId(session_id);
      } catch (err) {
        setError('Failed to create chat session');
        console.error(err);
      }
    };

    initSession();
  }, []);

  // Load chat history when session is created
  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId) return;

      try {
        const { history } = await getChatHistory(sessionId);
        setMessages(history);
      } catch (err) {
        setError('Failed to load chat history');
        console.error(err);
      }
    };

    loadHistory();
  }, [sessionId]);

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  };

  const clearHistory = async () => {
    if (!sessionId) return;

    try {
      await clearChatHistory(sessionId);
      setMessages([]);
    } catch (err) {
      setError('Failed to clear chat history');
      console.error(err);
    }
  };

  return {
    sessionId,
    messages,
    isLoading,
    error,
    addMessage,
    clearHistory,
    setError,
    setIsLoading
  };
}; 