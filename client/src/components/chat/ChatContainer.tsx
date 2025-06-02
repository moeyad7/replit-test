import React, { useState, useRef, useEffect } from 'react';
import { useChatSession } from '../../hooks/useChatSession';
import { submitQuery, ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import { ChatMessage } from './ChatMessage';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export const ChatContainer: React.FC = () => {
  const [input, setInput] = useState('');
  const { sessionId, messages, isLoading, error, addMessage, clearHistory, setIsLoading } = useChatSession();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;

    const question = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      const response = await submitQuery(question, sessionId);
      const message: ChatMessageType = {
        timestamp: Date.now() / 1000,
        question,
        response
      };
      addMessage(message);
    } catch (err) {
      console.error('Error submitting query:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {isLoading && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
              <LoadingSpinner />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="border-t p-4 bg-white shadow-lg">
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow duration-200"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
            >
              {isLoading ? 'Processing...' : 'Send'}
            </button>
          </div>
          {error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
              {error}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}; 