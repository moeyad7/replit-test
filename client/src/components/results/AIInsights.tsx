import { 
  AIIcon, 
  RefreshIcon, 
  AlertCircleIcon
} from "@/components/ui/icons";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

interface AIInsightsProps {
  isLoading: boolean;
  agent_response: string | null;
  onRefresh: () => void;
  error?: {
    type: string;
    message: string;
  };
}

export default function AIInsights({ isLoading, agent_response, onRefresh, error }: AIInsightsProps) {  
  if (!isLoading && !agent_response && !error) return null;
    
  return (
    <div className="bg-white rounded-lg shadow-sm h-full">
      <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AIIcon size={18} className={error ? "text-red-500" : "text-secondary-500"} />
          <h2 className="text-sm font-medium text-gray-800">
            {error ? "Error" : "AI Analysis"}
          </h2>
        </div>
        <div>
          <button 
            className="text-gray-400 hover:text-gray-600"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <RefreshIcon size={16} />
          </button>
        </div>
      </div>
      <div className="p-4">
        {error ? (
          // Error state
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircleIcon size={32} className="text-red-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Unable to Process Request</h3>
            <p className="text-sm text-gray-600 mb-4">{error.message}</p>
            <Button 
              variant="outline" 
              className="flex items-center justify-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              onClick={onRefresh}
            >
              <RefreshIcon size={16} className="mr-2" />
              Try Again
            </Button>
          </div>
        ) : isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ) : (
          <div className="text-gray-800 whitespace-pre-wrap">
            {agent_response || "No response available"}
          </div>
        )}
      </div>
    </div>
  );
}
