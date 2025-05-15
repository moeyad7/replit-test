import axios from "axios";

// Cache for storing DB schema
let schemaCache: any = null;

class QueryService {
  private apiBaseUrl: string;
  private apiKey: string;

  constructor() {
    // Get API URL and key from environment variables
    this.apiBaseUrl = process.env.DATABASE_API_URL || "https://api.loyalty-database.example.com";
    this.apiKey = process.env.DATABASE_API_KEY || "your-api-key";
    
    console.log(`Database API URL configured: ${this.apiBaseUrl}`);
    console.log(`Database API Key configured: ${this.apiKey ? "Yes (key provided)" : "No (using default key)"}`);
  }

  /**
   * Get the database schema
   */
  async getDatabaseSchema() {
    // Return cached schema if available
    if (schemaCache) {
      return schemaCache;
    }

    try {
      // Call your API to get the actual database schema
      // Replace this with your actual API endpoint
      const response = await axios.get(
        `${this.apiBaseUrl}/schema`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Cache the schema
      schemaCache = response.data;
      return response.data;
    } catch (error) {
      console.error("Error fetching database schema:", error);
      
      // Fallback schema if API call fails
      const fallbackSchema = {
        tables: [
          {
            name: "customers",
            description: "Customer information for loyalty program members",
            columns: [
              { name: "id", type: "integer", description: "Unique customer identifier" },
              { name: "first_name", type: "text", description: "Customer's first name" },
              { name: "last_name", type: "text", description: "Customer's last name" },
              { name: "email", type: "text", description: "Customer's email address" },
              { name: "created_at", type: "timestamp", description: "When the customer joined" },
              { name: "status", type: "text", description: "Account status (active, inactive)" }
            ]
          },
          {
            name: "points_transactions",
            description: "Records of points earned or redeemed by customers",
            columns: [
              { name: "id", type: "integer", description: "Unique transaction identifier" },
              { name: "customer_id", type: "integer", description: "References customers.id" },
              { name: "points", type: "integer", description: "Points earned (positive) or redeemed (negative)" },
              { name: "type", type: "text", description: "Transaction type (earn, redeem)" },
              { name: "category", type: "text", description: "Category (purchase, referral, challenge, social)" },
              { name: "created_at", type: "timestamp", description: "When the transaction occurred" }
            ]
          },
          {
            name: "challenges",
            description: "Loyalty program challenges that customers can complete to earn points",
            columns: [
              { name: "id", type: "integer", description: "Unique challenge identifier" },
              { name: "name", type: "text", description: "Challenge name" },
              { name: "description", type: "text", description: "Challenge description" },
              { name: "points", type: "integer", description: "Points awarded for completion" },
              { name: "start_date", type: "timestamp", description: "When the challenge starts" },
              { name: "end_date", type: "timestamp", description: "When the challenge ends" },
              { name: "status", type: "text", description: "Challenge status (active, completed, expired)" }
            ]
          },
          {
            name: "challenge_completions",
            description: "Records of challenges completed by customers",
            columns: [
              { name: "id", type: "integer", description: "Unique completion identifier" },
              { name: "customer_id", type: "integer", description: "References customers.id" },
              { name: "challenge_id", type: "integer", description: "References challenges.id" },
              { name: "completed_at", type: "timestamp", description: "When the challenge was completed" },
              { name: "points_awarded", type: "integer", description: "Points awarded for completion" }
            ]
          }
          // Add your additional tables here as needed
        ]
      };

      schemaCache = fallbackSchema;
      return fallbackSchema;
    }
  }

  /**
   * Execute a SQL query against the database
   */
  async executeQuery(sqlQuery: string) {
    try {
      // Make an API call to execute the query against your actual database
      const response = await axios.post(
        `${this.apiBaseUrl}/execute-query`,
        { query: sqlQuery },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Return the data from the API response
      return response.data;
    } catch (error) {
      console.error("Error executing query:", error);
      
      // If API call fails, fallback to mock data for testing/demo purposes
      console.log("API call failed, falling back to mock data");
      
      // Extract key information from the query to determine what mock data to return
      const lowerQuery = sqlQuery.toLowerCase();
      
      if (lowerQuery.includes("top") && lowerQuery.includes("points")) {
        // Return mock data for top points earners
        return this.getMockTopPointsEarners();
      } else if (lowerQuery.includes("expiring")) {
        // Return mock data for points expiring soon
        return this.getMockExpiringPoints();
      } else if (lowerQuery.includes("challenge") && lowerQuery.includes("completion")) {
        // Return mock data for challenge completion rates
        return this.getMockChallengeCompletions();
      } else {
        // Default to top points earners if we can't determine
        return this.getMockTopPointsEarners();
      }
    }
  }

  /**
   * Mock data generators
   */
  private getMockTopPointsEarners() {
    return [
      { id: 1, firstName: "Michael", lastName: "Scott", email: "mscott@example.com", points: 3542 },
      { id: 2, firstName: "Jim", lastName: "Halpert", email: "jhalpert@example.com", points: 2891 },
      { id: 3, firstName: "Pam", lastName: "Beesly", email: "pbeesly@example.com", points: 2745 },
      { id: 4, firstName: "Dwight", lastName: "Schrute", email: "dschrute@example.com", points: 2103 },
      { id: 5, firstName: "Kelly", lastName: "Kapoor", email: "kkapoor@example.com", points: 1986 }
    ];
  }

  private getMockExpiringPoints() {
    return [
      { id: 6, firstName: "Andy", lastName: "Bernard", email: "abernard@example.com", points: 1275, expiryDate: "2023-07-15" },
      { id: 7, firstName: "Stanley", lastName: "Hudson", email: "shudson@example.com", points: 950, expiryDate: "2023-07-18" },
      { id: 8, firstName: "Phyllis", lastName: "Vance", email: "pvance@example.com", points: 875, expiryDate: "2023-07-22" },
      { id: 9, firstName: "Kevin", lastName: "Malone", email: "kmalone@example.com", points: 650, expiryDate: "2023-07-25" },
      { id: 10, firstName: "Oscar", lastName: "Martinez", email: "omartinez@example.com", points: 590, expiryDate: "2023-07-28" }
    ];
  }

  private getMockChallengeCompletions() {
    return [
      { id: 1, name: "Summer Bonus", completions: 542, totalParticipants: 1200, completionRate: 45.2 },
      { id: 2, name: "Referral Drive", completions: 321, totalParticipants: 800, completionRate: 40.1 },
      { id: 3, name: "Social Media", completions: 268, totalParticipants: 600, completionRate: 44.7 },
      { id: 4, name: "First Purchase", completions: 189, totalParticipants: 250, completionRate: 75.6 },
      { id: 5, name: "Loyalty Anniversary", completions: 143, totalParticipants: 200, completionRate: 71.5 }
    ];
  }
}

export const queryService = new QueryService();
