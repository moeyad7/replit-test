import axios from 'axios';

interface QueryApiResponse {
  data: any[];
  metadata?: {
    count: number;
    executionTime: number;
  };
  error?: string;
}

/**
 * Client for interacting with the SQL query API
 */
export class ApiClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor() {
    // Load configuration from environment variables
    this.baseUrl = process.env.DATABASE_API_URL || 'https://example.com';
    this.apiKey = process.env.DATABASE_API_KEY || '';
    this.timeout = parseInt(process.env.API_TIMEOUT || '30000', 10);
  }

  /**
   * Executes a SQL query by sending a GET request to the API
   * @param sqlQuery The SQL query to execute
   * @returns The query results and metadata
   */
  async executeQuery(sqlQuery: string): Promise<QueryApiResponse> {
    try {
      console.log(`Executing query: ${sqlQuery}`);
      
      const response = await axios.get(`${this.baseUrl}/query`, {
        params: { query: sqlQuery },
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'User-Agent': 'Loyalty-Insights-Agent/1.0'
        },
        timeout: this.timeout
      });
      
      return {
        data: response.data.results || [],
        metadata: {
          count: response.data.count || 0,
          executionTime: response.data.time || 0
        }
      };
    } catch (error: any) {
      console.error('Error executing query:', error?.message || 'Unknown error');
      
      if (axios.isAxiosError(error)) {
        if (error.response) {
          // The server responded with a status code outside the 2xx range
          console.error(`API Error ${error.response.status}: ${error.response.statusText}`);
          console.error('Response data:', error.response.data);
          return {
            data: [],
            error: `API responded with error: ${error.response.status} ${error.response.statusText}`
          };
        } else if (error.request) {
          // The request was made but no response was received
          console.error('No response received from API');
          return {
            data: [],
            error: 'No response received from API. Please check your connection and API endpoint.'
          };
        }
      }
      
      return {
        data: [],
        error: `Error executing query: ${error?.message || 'Unknown error'}`
      };
    }
  }
}