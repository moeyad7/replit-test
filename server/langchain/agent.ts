import { createSqlGenerationChain, createInsightsGenerationChain } from './chains';
import { createSqlQueryTool, createMockDataTool } from './tools';
import { loadDatabaseSchema } from '../schema/schemaLoader';

interface QueryUnderstanding {
  understanding: string;
}

interface Insight {
  id: number;
  text: string;
}

interface Recommendation {
  id: number;
  title: string;
  description: string;
  type: 'email' | 'award' | 'other' | string;
}

interface QueryResult {
  queryUnderstanding: string;
  sqlQuery: string;
  databaseResults: {
    count: number;
    time: number;
  };
  title: string;
  data: any[];
  insights: Insight[];
  recommendations: Recommendation[];
}

/**
 * LoyaltyAgent processes natural language questions using LangChain
 * to generate SQL, execute it, and provide insights
 */
export class LoyaltyAgent {
  private sqlChain;
  private insightsChain;
  private sqlTool;
  private mockDataTool;

  constructor() {
    // Initialize chains and tools
    this.sqlChain = createSqlGenerationChain();
    this.insightsChain = createInsightsGenerationChain();
    this.sqlTool = createSqlQueryTool();
    this.mockDataTool = createMockDataTool();
    
    console.log('LoyaltyAgent initialized with LangChain components');
  }

  /**
   * Process a natural language question about loyalty program data
   */
  async processQuestion(question: string): Promise<QueryResult> {
    try {
      console.log(`Processing question: ${question}`);
      
      // Step 1: Generate SQL from the question
      const sqlQuery = await this.sqlChain.invoke({
        question
      });
      
      console.log(`Generated SQL: ${sqlQuery}`);
      
      // Step 2: Execute the SQL query
      let queryResults;
      let isError = false;
      
      try {
        const resultsJson = await this.sqlTool.invoke(sqlQuery);
        queryResults = JSON.parse(resultsJson);
        
        if (queryResults.error) {
          console.warn(`SQL execution error: ${queryResults.error}`);
          isError = true;
        }
      } catch (error) {
        console.error('Error executing SQL query:', error);
        queryResults = { error: 'Failed to execute query', data: [] };
        isError = true;
      }
      
      // If there was an error, try using mock data
      if (isError || !queryResults.data || queryResults.data.length === 0) {
        console.log('Using mock data due to API error or empty results');
        
        // Determine which mock data to use based on the query
        const sqlLower = sqlQuery.toLowerCase();
        let mockType = 'customers';
        
        if (sqlLower.includes('points_transactions') || sqlLower.includes('transaction')) {
          mockType = 'transactions';
        } else if (sqlLower.includes('challenges') && !sqlLower.includes('challenge_completions')) {
          mockType = 'challenges';
        } else if (sqlLower.includes('challenge_completions') || sqlLower.includes('completion')) {
          mockType = 'completions';
        }
        
        const mockResultsJson = await this.mockDataTool.invoke(mockType);
        queryResults = JSON.parse(mockResultsJson);
      }
      
      // Prepare results for insights generation
      const data = queryResults.data || [];
      const metadata = queryResults.metadata || { count: data.length, executionTime: 0 };
      
      // Step 3: Generate insights from the results
      let insights = {
        title: "Data Analysis",
        insights: [],
        recommendations: []
      };
      
      try {
        const insightsJson = await this.insightsChain.invoke({
          question,
          sqlQuery,
          results: JSON.stringify(data)
        });
        
        try {
          const parsed = JSON.parse(insightsJson);
          insights = {
            title: parsed.title || "Data Analysis",
            insights: parsed.insights || [],
            recommendations: parsed.recommendations || []
          };
        } catch (parseError) {
          console.error('Error parsing insights JSON:', parseError);
          insights = {
            title: "Data Analysis",
            insights: [{ id: 1, text: "Unable to parse insights from the analysis." }],
            recommendations: [{ 
              id: 1, 
              title: "Retry Query", 
              description: "Please try rephrasing your question for better results.",
              type: "other"
            }]
          };
        }
      } catch (error: any) {
        console.error('Error generating insights:', error);
        insights = {
          title: "Data Analysis",
          insights: [{ id: 1, text: "Unable to generate insights from the data." }],
          recommendations: [{ 
            id: 1, 
            title: "Review Query", 
            description: "The current query may not be providing enough data for meaningful analysis.",
            type: "other"
          }]
        };
      }
      
      // Step 4: Return the complete result
      return {
        queryUnderstanding: this.extractQueryUnderstanding(question),
        sqlQuery,
        databaseResults: {
          count: metadata.count,
          time: metadata.executionTime
        },
        title: insights.title,
        data,
        insights: insights.insights,
        recommendations: insights.recommendations
      };
    } catch (error: any) {
      console.error('Error in LoyaltyAgent:', error);
      
      // Return a fallback response
      return {
        queryUnderstanding: "There was an error understanding your question.",
        sqlQuery: "",
        databaseResults: {
          count: 0,
          time: 0
        },
        title: "Error Processing Query",
        data: [],
        insights: [
          {
            id: 1,
            text: `Error: ${error?.message || 'Unknown error occurred'}`
          }
        ],
        recommendations: [
          {
            id: 1,
            title: "Try Again",
            description: "Please try rephrasing your question or ask something else.",
            type: "other"
          }
        ]
      };
    }
  }
  
  /**
   * Extract a human-readable understanding of the query
   * For now, this is a simple placeholder as the main understanding
   * is handled in the SQL generation chain
   */
  private extractQueryUnderstanding(question: string): string {
    return `I'm looking for loyalty program data that answers: "${question}"`;
  }
}