import React, { useState, useRef, useEffect } from 'react';
import { useChatSession } from '../../hooks/useChatSession';
import { submitQuery, ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import { ChatMessage } from './ChatMessage';

export const ChatContainer: React.FC = () => {
  const [input, setInput] = useState('');
  const { sessionId, messages, isLoading, error, addMessage, clearHistory } = useChatSession();
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
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-xl font-semibold">Chat Session</h2>
        <button
          onClick={clearHistory}
          className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
        >
          Clear History
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="border-t p-4 bg-white">
        <div className="flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your loyalty program data..."
            className="flex-1 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : 'Send'}
          </button>
        </div>
        {error && (
          <div className="mt-2 text-sm text-red-600">
            {error}
          </div>
        )}
      </form>
    </div>
  );
}; 