import React from 'react';
import { ChatMessage as ChatMessageType } from '../../pythonBackendProxy';
import { format } from 'date-fns';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { question, response, timestamp } = message;

  return (
    <div className="mb-8 space-y-4">
      {/* Question */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="text-sm text-gray-500 mb-2">
          {format(timestamp * 1000, 'MMM d, yyyy h:mm a')}
        </div>
        <div className="font-medium text-blue-900">{question}</div>
      </div>

      {/* Response */}
      <div className="bg-white p-4 rounded-lg shadow">
        {/* Query Understanding */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Understanding</h3>
          <p className="text-gray-700">{response.queryUnderstanding}</p>
        </div>

        {/* SQL Query */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">SQL Query</h3>
          <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
            {response.sqlQuery}
          </pre>
        </div>

        {/* Results Summary */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Results</h3>
          <p className="text-gray-700">
            Found {response.databaseResults.count} results in {response.databaseResults.time.toFixed(2)}s
          </p>
        </div>

        {/* Insights */}
        {response.insights.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Insights</h3>
            <ul className="list-disc list-inside space-y-1">
              {response.insights.map(insight => (
                <li key={insight.id} className="text-gray-700">{insight.text}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {response.recommendations.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Recommendations</h3>
            <ul className="space-y-2">
              {response.recommendations.map(rec => (
                <li key={rec.id} className="bg-gray-50 p-3 rounded">
                  <h4 className="font-medium text-gray-900">{rec.title}</h4>
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