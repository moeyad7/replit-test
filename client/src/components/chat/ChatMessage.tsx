import React from 'react';
import { ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import ReactMarkdown from 'react-markdown';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { question, response } = message;

  return (
    <div className="mb-8 space-y-6 max-w-4xl mx-auto">
      {/* Question */}
      <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
        <div className="flex items-center mb-2">
          <svg className="w-5 h-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span className="text-sm font-medium text-blue-600">Question</span>
        </div>
        <div className="text-gray-800 text-lg">{question}</div>
      </div>

      {/* Response */}
      <div className={`p-6 rounded-xl border ${response.is_error ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
        <div className="flex items-center mb-3">
          {response.is_error ? (
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          <span className={`text-sm font-medium ${response.is_error ? 'text-red-600' : 'text-green-600'}`}>
            {response.is_error ? 'Error' : 'Response'}
          </span>
        </div>
        <div className={`prose prose-sm max-w-none ${response.is_error ? 'text-red-600' : 'text-gray-800'}`}>
          <ReactMarkdown>
            {response.agent_response || "No response available"}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}; 