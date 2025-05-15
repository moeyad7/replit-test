import React from "react";
import { 
  TranslateIcon, 
  CodeIcon, 
  DatabaseIcon, 
  CheckCircleIcon,
  InfoIcon
} from "@/components/ui/icons";
import { 
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface ProcessingStepsProps {
  queryUnderstanding: string | null;
  sqlQuery: string | null;
  databaseResults: { count: number; time: number } | null;
  isLoading: boolean;
  showProcessing: boolean;
}

export default function ProcessingSteps({ 
  queryUnderstanding, 
  sqlQuery, 
  databaseResults, 
  isLoading,
  showProcessing
}: ProcessingStepsProps) {
  
  if (!showProcessing) return null;

  const statusIndicator = (completed: boolean) => (
    <span className={`text-xs px-2 py-0.5 rounded-full flex items-center ${
      completed ? "text-green-600 bg-green-50" : "text-amber-600 bg-amber-50"
    }`}>
      {completed ? (
        <>
          <CheckCircleIcon size={12} className="mr-1" /> Complete
        </>
      ) : (
        <>
          <span className="mr-1">●</span> Processing
        </>
      )}
    </span>
  );

  return (
    <section className="mb-6">
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-800">Query Processing</h2>
          <div className="flex items-center space-x-2">
            {!isLoading && databaseResults ? (
              statusIndicator(true)
            ) : (
              statusIndicator(false)
            )}
            <button className="text-gray-400 hover:text-gray-600">
              <InfoIcon size={16} />
            </button>
          </div>
        </div>
        
        {/* Query to SQL Generation */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-start">
            <div className={`flex-shrink-0 rounded-full w-6 h-6 flex items-center justify-center mt-0.5 ${
              queryUnderstanding ? "bg-green-100 text-green-600" : "bg-amber-100 text-amber-600"
            }`}>
              <TranslateIcon size={12} />
            </div>
            <div className="ml-3">
              <h3 className="text-xs font-medium text-gray-700">Query Understanding</h3>
              {queryUnderstanding ? (
                <p className="mt-1 text-xs text-gray-500">{queryUnderstanding}</p>
              ) : (
                <p className="mt-1 text-xs text-gray-500">Analyzing your question...</p>
              )}
            </div>
          </div>
        </div>

        {/* SQL Query Generated */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-start">
            <div className={`flex-shrink-0 rounded-full w-6 h-6 flex items-center justify-center mt-0.5 ${
              sqlQuery ? "bg-green-100 text-green-600" : "bg-amber-100 text-amber-600"
            }`}>
              <CodeIcon size={12} />
            </div>
            <div className="ml-3 w-full">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-medium text-gray-700">SQL Query Generated</h3>
                {sqlQuery && (
                  <Collapsible>
                    <CollapsibleTrigger className="text-xs text-primary-600 hover:text-primary-700">
                      View Full Query
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <div className="mt-1 bg-gray-50 rounded p-2 text-xs font-mono text-gray-600 overflow-x-auto">
                        <pre>{sqlQuery}</pre>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                )}
              </div>
              {sqlQuery ? (
                <div className="mt-1 bg-gray-50 rounded p-2 text-xs font-mono text-gray-600 overflow-x-auto line-clamp-3">
                  <code>
                    {sqlQuery}
                  </code>
                </div>
              ) : (
                <p className="mt-1 text-xs text-gray-500">Generating SQL query...</p>
              )}
            </div>
          </div>
        </div>

        {/* API Response */}
        <div className="p-4">
          <div className="flex items-start">
            <div className={`flex-shrink-0 rounded-full w-6 h-6 flex items-center justify-center mt-0.5 ${
              databaseResults ? "bg-green-100 text-green-600" : "bg-amber-100 text-amber-600"
            }`}>
              <DatabaseIcon size={12} />
            </div>
            <div className="ml-3">
              <h3 className="text-xs font-medium text-gray-700">Database Results</h3>
              {databaseResults ? (
                <p className="mt-1 text-xs text-gray-500">
                  Retrieved {databaseResults.count} {databaseResults.count === 1 ? 'record' : 'records'} in {databaseResults.time} seconds
                </p>
              ) : (
                <p className="mt-1 text-xs text-gray-500">Fetching data from database...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
