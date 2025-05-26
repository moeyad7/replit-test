import { 
  AIIcon, 
  RefreshIcon, 
  InfoIcon,
  MailIcon,
  AwardIcon,
  PieChartIcon,
  FileTextIcon,
  AlertCircleIcon
} from "@/components/ui/icons";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Insight, Recommendation } from "@/lib/types";

interface AIInsightsProps {
  isLoading: boolean;
  insights: Insight[] | null;
  recommendations: Recommendation[] | null;
  onRefresh: () => void;
  error?: {
    type: string;
    message: string;
  };
}

export default function AIInsights({ isLoading, insights, recommendations, onRefresh, error }: AIInsightsProps) {  
  if (!isLoading && !insights && !recommendations && !error) return null;
    
  return (
    <div className="bg-white rounded-lg shadow-sm h-full">
      <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AIIcon size={18} className={error ? "text-red-500" : "text-secondary-500"} />
          <h2 className="text-sm font-medium text-gray-800">
            {error ? "Error" : "AI Analysis & Insights"}
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
      <div className="p-4 space-y-4">
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
        ) : (
          <>
            {/* Key Findings */}
            <div>
              <h3 className="text-sm font-medium text-gray-800 mb-2">Key Findings</h3>
              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-start">
                      <Skeleton className="h-4 w-4 mr-2 mt-0.5" />
                      <Skeleton className="h-4 flex-1" />
                    </div>
                  ))}
                </div>
              ) : insights && insights.length > 0 ? (
                <ul className="space-y-2 text-sm text-gray-600">
                  {insights.map((insight, index) => (
                    <li key={index} className="flex items-start">
                      <InfoIcon size={16} className="text-primary-600 mt-0.5 mr-2" />
                      <span dangerouslySetInnerHTML={{ __html: insight.text }} />
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">No insights available for this query.</p>
              )}
            </div>

            {/* Recommendations */}
            {(isLoading || (recommendations && recommendations.length > 0)) && (
              <div className="border-t border-gray-100 pt-4">
                <h3 className="text-sm font-medium text-gray-800 mb-2">Recommendations</h3>
                {isLoading ? (
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="flex items-start">
                        <Skeleton className="h-6 w-6 rounded-full mr-3 mt-0.5" />
                        <div className="space-y-1 flex-1">
                          <Skeleton className="h-4 w-24" />
                          <Skeleton className="h-4 w-full" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : recommendations && recommendations.length > 0 ? (
                  <ul className="space-y-3 text-sm text-gray-600">
                    {recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start">
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full ${
                          index === 0 ? 'bg-secondary-500' : 'bg-amber-500'
                        } flex items-center justify-center text-white mt-0.5`}>
                          {index === 0 ? <MailIcon size={12} /> : <AwardIcon size={12} />}
                        </div>
                        <div className="ml-3">
                          <p className="font-medium text-gray-700">{rec.title}</p>
                          <p className="mt-1">{rec.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            )}

            {/* Charts section - placeholder */}
            {(isLoading || (insights && insights.length > 0)) && (
              <div className="border-t border-gray-100 pt-4">
                <h3 className="text-sm font-medium text-gray-800 mb-2">Points Categories Breakdown</h3>
                {isLoading ? (
                  <Skeleton className="h-48 w-full rounded" />
                ) : (
                  <div className="h-48 flex items-center justify-center bg-gray-50 rounded">
                    <div className="text-center">
                      <PieChartIcon size={32} className="mx-auto text-gray-400 mb-2" />
                      <p className="text-xs text-gray-500">Points category distribution chart</p>
                    </div>
                  </div>
                )}
                {!isLoading && (
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center">
                      <span className="w-3 h-3 bg-primary-400 rounded-full mr-2"></span>
                      <span className="text-gray-600">Purchases (64%)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="w-3 h-3 bg-blue-400 rounded-full mr-2"></span>
                      <span className="text-gray-600">Referrals (18%)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="w-3 h-3 bg-green-400 rounded-full mr-2"></span>
                      <span className="text-gray-600">Challenges (12%)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="w-3 h-3 bg-purple-400 rounded-full mr-2"></span>
                      <span className="text-gray-600">Social (6%)</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
      {!isLoading && !error && (insights || recommendations) && (
        <div className="border-t border-gray-200 p-4">
          <Button 
            variant="outline" 
            className="w-full flex items-center justify-center px-4 py-2 border border-primary-300 text-sm font-medium rounded-md text-primary-700 bg-primary-50 hover:bg-primary-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <FileTextIcon size={16} className="mr-2" />
            Generate Full Report
          </Button>
        </div>
      )}
    </div>
  );
}
