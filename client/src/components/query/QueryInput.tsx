import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CloseIcon, SearchIcon } from "@/components/ui/icons";
import { useToast } from "@/hooks/use-toast";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  "Top spending customers",
  "Points expiring soon",
  "Challenge completion rates"
];

export default function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [query, setQuery] = useState<string>("");
  const { toast } = useToast();

  const handleSubmit = () => {
    if (!query.trim()) {
      toast({
        title: "Empty query",
        description: "Please enter a question about your loyalty data.",
        variant: "destructive"
      });
      return;
    }
    
    onSubmit(query);
  };

  const handleClear = () => {
    setQuery("");
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <section className="mb-6">
      <div className="bg-white rounded-lg shadow-sm p-4">
        <h2 className="text-lg font-medium text-gray-800 mb-3">Ask about your loyalty data</h2>
        <div className="relative">
          <div className="flex">
            <div className="relative flex-grow">
              <Input
                type="text"
                className="pr-10 py-3"
                placeholder="e.g., 'How many points did our customers earn last month?'"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSubmit();
                  }
                }}
              />
              {query && (
                <button 
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  onClick={handleClear}
                >
                  <CloseIcon size={16} />
                </button>
              )}
            </div>
            <Button 
              className="ml-2 bg-primary" 
              onClick={handleSubmit}
              disabled={isLoading}
            >
              <SearchIcon size={16} className="mr-1" />
              <span>Ask</span>
            </Button>
          </div>
          <div className="mt-2">
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((example, index) => (
                <button 
                  key={index}
                  className="text-xs bg-gray-100 px-3 py-1 rounded-full text-gray-600 hover:bg-gray-200"
                  onClick={() => handleExampleClick(example)}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
