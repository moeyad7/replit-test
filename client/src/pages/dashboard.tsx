import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import QueryInput from "@/components/query/QueryInput";
import ProcessingSteps from "@/components/query/ProcessingSteps";
import ResultsTable from "@/components/results/ResultsTable";
import AIInsights from "@/components/results/AIInsights";
import { QueryResponse } from "@/lib/types";

export default function Dashboard() {
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [showProcessing, setShowProcessing] = useState(false);
  const { toast } = useToast();

  const queryMutation = useMutation({
    mutationFn: async (query: string) => {
      const res = await apiRequest("POST", "/api/query", { query });
      return res.json();
    },
    onSuccess: (data: QueryResponse) => {
      setQueryResponse(data);
    },
    onError: (error) => {
      toast({
        title: "Error processing query",
        description: error.message || "Something went wrong while processing your query.",
        variant: "destructive"
      });
    }
  });

  const handleSubmitQuery = (query: string) => {
    setShowProcessing(true);
    queryMutation.mutate(query);
  };

  const handleRefreshInsights = () => {
    if (queryResponse) {
      // Refresh insights with the same data
      toast({
        title: "Refreshing insights",
        description: "Getting fresh insights based on your query results...",
      });
    }
  };

  return (
    <>
      <QueryInput 
        onSubmit={handleSubmitQuery} 
        isLoading={queryMutation.isPending} 
      />
      
      <ProcessingSteps 
        queryUnderstanding={queryResponse?.queryUnderstanding || null}
        sqlQuery={queryResponse?.sqlQuery || null}
        databaseResults={queryResponse?.databaseResults || null}
        isLoading={queryMutation.isPending}
        showProcessing={showProcessing}
      />
      
      {(queryMutation.isPending || queryResponse) && (
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ResultsTable 
              title={queryResponse?.title || "Loading Results..."}
              data={queryResponse?.data || []}
              isLoading={queryMutation.isPending}
            />
          </div>
          
          <div className="lg:col-span-1">
            <AIInsights 
              isLoading={queryMutation.isPending}
              insights={queryResponse?.insights || null}
              recommendations={queryResponse?.recommendations || null}
              onRefresh={handleRefreshInsights}
            />
          </div>
        </section>
      )}
    </>
  );
}
