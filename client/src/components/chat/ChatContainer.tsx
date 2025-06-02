import React, { useState, useRef, useEffect } from 'react';
import { useChatSession } from '../../hooks/useChatSession';
import { submitQuery, ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import { ChatMessage } from './ChatMessage';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export const ChatContainer: React.FC = () => {
  const [input, setInput] = useState('');
  const { sessionId, messages, isLoading, error, addMessage, clearHistory, setIsLoading } = useChatSession();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;

    const question = input.trim();
    setInput('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gradient-to-b from-gray-50/50 to-white">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="text-6xl mb-4">👋</div>
              <h2 className="text-xl font-semibold text-gray-700">Welcome to the AI Assistant</h2>
              <p className="text-gray-500 max-w-md mx-auto">
                I'm here to help! Ask me anything and I'll do my best to assist you.
              </p>
            </div>
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className="animate-fade-in">
            <ChatMessage message={message} />
          </div>
        ))}
        {isLoading && (
          <div className="max-w-4xl mx-auto animate-fade-in">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <LoadingSpinner />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 bg-white/80 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col space-y-3">
            <div className="flex items-end space-x-4">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message here... (Press Enter to send, Shift + Enter for new line)"
                  className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm hover:shadow-md resize-none min-h-[44px] max-h-[150px]"
                  disabled={isLoading}
                  rows={1}
                />
                <div className="absolute right-3 bottom-3 text-xs text-gray-400">
                  {input.length > 0 && `${input.length} characters`}
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md flex items-center space-x-2 h-[44px]"
              >
                <span>{isLoading ? 'Processing...' : 'Send'}</span>
                {!isLoading && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                )}
              </button>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500 px-1">
              <div className="flex items-center space-x-4">
                <button
                  type="button"
                  onClick={() => clearHistory()}
                  className="hover:text-gray-700 transition-colors duration-200 flex items-center space-x-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <span>Clear chat</span>
                </button>
                <span className="text-gray-300">|</span>
                <span>Press Enter to send</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-block w-2 h-2 bg-green-400 rounded-full"></span>
                <span>AI Assistant is ready</span>
              </div>
            </div>
          </div>
          {error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100 animate-shake">
              {error}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}; 