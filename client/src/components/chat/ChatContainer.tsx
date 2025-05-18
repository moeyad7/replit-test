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
      {/* Chat Header */}
      <div className="bg-white border-b p-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center">
          <svg className="w-6 h-6 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-800">Chat Session</h2>
        </div>
        <button
          onClick={clearHistory}
          className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200 flex items-center"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear History
        </button>
      </div>

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
              placeholder="Ask a question about your loyalty program data..."
              className="flex-1 p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow duration-200"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 flex items-center"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Send
                </>
              )}
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