import { DynamicTool } from "@langchain/core/tools";
import { ApiClient } from "./apiClient";

/**
 * Create a tool for executing SQL queries via the API endpoint
 */
export function createSqlQueryTool() {
  const apiClient = new ApiClient();
  
  return new DynamicTool({
    name: "execute_sql_query",
    description: "Executes a SQL query against the loyalty program database using a REST API endpoint. The input should be a valid SQL query string.",
    func: async (sqlQuery: string) => {
      try {
        // Validate that input is a SQL query
        if (!sqlQuery.trim().toLowerCase().startsWith('select')) {
          return JSON.stringify({
            error: "Only SELECT queries are allowed for security reasons."
          });
        }
        
        // Execute the query
        const response = await apiClient.executeQuery(sqlQuery);
        
        if (response.error) {
          return JSON.stringify({
            error: response.error,
            data: []
          });
        }
        
        // Return the results
        return JSON.stringify({
          data: response.data,
          metadata: response.metadata
        });
      } catch (error: any) {
        console.error('Error in SQL Query tool:', error);
        return JSON.stringify({
          error: `Error executing query: ${error?.message || 'Unknown error'}`,
          data: []
        });
      }
    }
  });
}

/**
 * Mock database data generator for testing when the API is not available
 */
export function createMockDataTool() {
  return new DynamicTool({
    name: "get_mock_data",
    description: "Generates mock data for testing when the database API is not available. Input should be the type of data needed: 'customers', 'transactions', 'challenges', or 'completions'.",
    func: async (dataType: string) => {
      const type = dataType.toLowerCase().trim();
      
      let data: any[] = [];
      
      if (type === 'customers' || type === 'customer') {
        data = getMockCustomers();
      } else if (type === 'transactions' || type === 'points' || type === 'points_transactions') {
        data = getMockTransactions();
      } else if (type === 'challenges' || type === 'challenge') {
        data = getMockChallenges();
      } else if (type === 'completions' || type === 'challenge_completions') {
        data = getMockChallengeCompletions();
      } else {
        return JSON.stringify({
          error: `Unknown data type: ${dataType}. Valid types are: customers, transactions, challenges, completions.`
        });
      }
      
      return JSON.stringify({
        data,
        metadata: {
          count: data.length,
          executionTime: 0
        }
      });
    }
  });
}

// Mock data generators
function getMockCustomers() {
  return [
    { id: 1, first_name: "Michael", last_name: "Scott", email: "mscott@example.com", points: 3542, created_at: "2023-01-15" },
    { id: 2, first_name: "Jim", last_name: "Halpert", email: "jhalpert@example.com", points: 2891, created_at: "2023-01-20" },
    { id: 3, first_name: "Pam", last_name: "Beesly", email: "pbeesly@example.com", points: 2745, created_at: "2023-01-22" },
    { id: 4, first_name: "Dwight", last_name: "Schrute", email: "dschrute@example.com", points: 2103, created_at: "2023-02-01" },
    { id: 5, first_name: "Kelly", last_name: "Kapoor", email: "kkapoor@example.com", points: 1986, created_at: "2023-02-15" }
  ];
}

function getMockTransactions() {
  return [
    { id: 1, customer_id: 1, points: 500, transaction_date: "2023-05-01", expiry_date: "2024-05-01", source: "purchase", description: "Online purchase" },
    { id: 2, customer_id: 1, points: 200, transaction_date: "2023-05-15", expiry_date: "2024-05-15", source: "referral", description: "Friend referral" },
    { id: 3, customer_id: 2, points: 350, transaction_date: "2023-05-05", expiry_date: "2024-05-05", source: "purchase", description: "In-store purchase" },
    { id: 4, customer_id: 3, points: -150, transaction_date: "2023-05-20", expiry_date: null, source: "redemption", description: "Gift card redemption" },
    { id: 5, customer_id: 4, points: 425, transaction_date: "2023-05-10", expiry_date: "2024-05-10", source: "purchase", description: "Mobile app purchase" }
  ];
}

function getMockChallenges() {
  return [
    { id: 1, name: "Summer Bonus", description: "Make 3 purchases in June", points: 500, start_date: "2023-06-01", end_date: "2023-06-30", active: true },
    { id: 2, name: "Referral Drive", description: "Refer a friend to join our program", points: 300, start_date: "2023-05-01", end_date: "2023-07-31", active: true },
    { id: 3, name: "Social Media", description: "Share your purchase on social media", points: 150, start_date: "2023-04-15", end_date: "2023-08-15", active: true },
    { id: 4, name: "First Purchase", description: "Complete your first purchase", points: 200, start_date: "2023-01-01", end_date: "2023-12-31", active: true },
    { id: 5, name: "Loyalty Anniversary", description: "Celebrate your 1-year membership", points: 500, start_date: "2023-01-01", end_date: "2023-12-31", active: true }
  ];
}

function getMockChallengeCompletions() {
  return [
    { id: 1, customer_id: 1, challenge_id: 1, completion_date: "2023-06-15", points_awarded: 500 },
    { id: 2, customer_id: 1, challenge_id: 4, completion_date: "2023-01-20", points_awarded: 200 },
    { id: 3, customer_id: 2, challenge_id: 2, completion_date: "2023-05-25", points_awarded: 300 },
    { id: 4, customer_id: 3, challenge_id: 3, completion_date: "2023-05-10", points_awarded: 150 },
    { id: 5, customer_id: 5, challenge_id: 4, completion_date: "2023-02-18", points_awarded: 200 }
  ];
}