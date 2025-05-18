import React from 'react';
import { ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import { format } from 'date-fns';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { question, response, timestamp } = message;

  return (
    <div className="mb-8 space-y-4 max-w-4xl mx-auto">
      {/* Question */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl shadow-sm">
        <div className="flex items-center text-sm text-gray-500 mb-2">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          {format(timestamp * 1000, 'MMM d, yyyy h:mm a')}
        </div>
        <div className="font-medium text-blue-900 text-lg">{question}</div>
      </div>

      {/* Response */}
      <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
        {/* Query Understanding */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Understanding
          </h3>
          <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{response.queryUnderstanding}</p>
        </div>

        {/* SQL Query */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
            SQL Query
          </h3>
          <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto font-mono border border-gray-200">
            {response.sqlQuery}
          </pre>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Results
          </h3>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-gray-700">
              Found <span className="font-semibold text-blue-600">{response.databaseResults.count}</span> results in{' '}
              <span className="font-semibold text-blue-600">{response.databaseResults.time.toFixed(2)}s</span>
            </p>
          </div>
        </div>

        {/* Insights */}
        {response.insights.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Insights
            </h3>
            <ul className="space-y-2">
              {response.insights.map(insight => (
                <li key={insight.id} className="bg-gray-50 p-3 rounded-lg border border-gray-200 text-gray-700">
                  {insight.text}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {response.recommendations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Recommendations
            </h3>
            <ul className="space-y-3">
              {response.recommendations.map(rec => (
                <li key={rec.id} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-1">{rec.title}</h4>
                  <p className="text-gray-700">{rec.description}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}; 