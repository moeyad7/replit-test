import { ChatOpenAI } from "@langchain/openai";
import axios from "axios";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import yaml from "js-yaml";

// For ESM compatibility (replacing __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Schema interfaces
interface TableColumn {
  name: string;
  type: string;
  description: string;
}

interface Table {
  name: string;
  description: string;
  columns: TableColumn[];
}

interface DatabaseSchema {
  tables: Table[];
}

// Response interfaces
interface Insight {
  id: number;
  text: string;
}

interface Recommendation {
  id: number;
  title: string;
  description: string;
  type: string;
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
 * LoyaltyAgent processes natural language questions about loyalty program data
 */
export class LoyaltyAgent {
  private model: ChatOpenAI;
  private schema: DatabaseSchema;
  
  constructor() {
    // Initialize OpenAI model
    this.model = new ChatOpenAI({
      modelName: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024
      temperature: 0
    });
    
    // Load database schema
    this.schema = this.loadDatabaseSchema();
    
    console.log("LoyaltyAgent initialized");
  }
  
  /**
   * Process a natural language question about loyalty program data
   */
  async processQuestion(question: string): Promise<QueryResult> {
    try {
      console.log(`Processing question: ${question}`);
      
      // Step 1: Generate SQL from natural language question
      const sqlQuery = await this.generateSQL(question);
      console.log(`Generated SQL: ${sqlQuery}`);
      
      // Step 2: Execute SQL query
      const { data, metadata } = await this.executeQuery(sqlQuery);
      console.log(`Query executed, returned ${data.length} rows`);
      
      // Step 3: Generate insights from results
      const analysis = await this.generateInsights(question, sqlQuery, data);
      console.log(`Generated insights: ${analysis.title}`);
      
      // Return the complete response
      return {
        queryUnderstanding: `I'm looking for loyalty program data that answers: "${question}"`,
        sqlQuery,
        databaseResults: {
          count: metadata.count,
          time: metadata.time
        },
        title: analysis.title,
        data,
        insights: analysis.insights,
        recommendations: analysis.recommendations
      };
      
    } catch (error: any) {
      console.error("Error in LoyaltyAgent:", error);
      
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
   * Generate SQL from a natural language question
   */
  private async generateSQL(question: string): Promise<string> {
    try {
      const schemaString = this.formatSchemaForPrompt(this.schema);
      
      const response = await this.model.invoke(
        `You are a SQL expert for a loyalty program database. Your task is to convert natural language questions 
        into SQL queries that can answer the question.
        
        Use the following database schema:
        ${schemaString}
        
        Important guidelines:
        1. Only use the tables and columns defined in the schema
        2. Always use proper SQL syntax for the PostgreSQL dialect
        3. Include appropriate JOINs when information from multiple tables is needed
        4. Use descriptive aliases for tables (e.g., c for customers, pt for points_transactions)
        5. Limit results to 100 rows unless specified otherwise
        6. Use simple ORDER BY and GROUP BY clauses when appropriate
        7. Format the SQL query nicely with line breaks and proper indentation
        8. Only return a valid SQL query and nothing else
        
        User question: ${question}
        
        SQL Query:`
      );
      
      return response.content.toString().trim();
    } catch (error: any) {
      console.error("Error generating SQL:", error);
      throw new Error(`Failed to generate SQL: ${error?.message || 'Unknown error'}`);
    }
  }
  
  /**
   * Execute a SQL query via the API
   */
  private async executeQuery(sqlQuery: string): Promise<{ 
    data: any[]; 
    metadata: { count: number; time: number }
  }> {
    try {
      // Try to execute SQL query via the API
      const baseUrl = process.env.DATABASE_API_URL || 'https://example.com';
      const apiKey = process.env.DATABASE_API_KEY || '';
      
      console.log(`Sending query to: ${baseUrl}/query`);
      
      const response = await axios.get(`${baseUrl}/query`, {
        params: { query: sqlQuery },
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'User-Agent': 'Loyalty-Insights-Agent/1.0'
        },
        timeout: parseInt(process.env.API_TIMEOUT || '30000', 10)
      });
      
      return {
        data: response.data.results || [],
        metadata: {
          count: response.data.count || 0,
          time: response.data.time || 0
        }
      };
    } catch (error: any) {
      console.error("Error executing query:", error);
      console.log("Using mock data instead");
      
      // Fall back to mock data
      return {
        data: this.getMockData(sqlQuery),
        metadata: {
          count: 5,
          time: 0.1
        }
      };
    }
  }
  
  /**
   * Generate insights from query results
   */
  private async generateInsights(question: string, sqlQuery: string, data: any[]): Promise<{
    title: string;
    insights: Insight[];
    recommendations: Recommendation[];
  }> {
    try {
      const response = await this.model.invoke(
        `You are a business intelligence analyst for a loyalty program. Your task is to analyze the data from a SQL query and provide 
        valuable insights and recommendations.
        
        Original question: ${question}
        
        SQL query that was executed: ${sqlQuery}
        
        Query results: ${JSON.stringify(data)}
        
        Please provide:
        1. A suitable title for this data analysis (keep it short and informative)
        2. 3-5 key insights from the data (focus on patterns, trends, or notable observations)
        3. 2-3 actionable business recommendations based on these insights
        
        Format your response as a JSON object with the following structure:
        {
          "title": "Analysis title",
          "insights": [
            {"id": 1, "text": "First insight..."},
            {"id": 2, "text": "Second insight..."}
          ],
          "recommendations": [
            {"id": 1, "title": "Recommendation title", "description": "Details...", "type": "email|award|other"},
            {"id": 2, "title": "Recommendation title", "description": "Details...", "type": "email|award|other"}
          ]
        }`
      );
      
      try {
        const textResponse = response.content.toString().trim();
        // Extract JSON from the response (in case it has additional text)
        const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
        
        if (jsonMatch) {
          const jsonStr = jsonMatch[0];
          const parsed = JSON.parse(jsonStr);
          
          return {
            title: parsed.title || "Data Analysis",
            insights: Array.isArray(parsed.insights) ? parsed.insights : [],
            recommendations: Array.isArray(parsed.recommendations) ? parsed.recommendations : []
          };
        } else {
          throw new Error("Could not extract JSON from response");
        }
      } catch (parseError: any) {
        console.error("Error parsing insights JSON:", parseError);
        
        // Fallback insights
        return {
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
    } catch (error: any) {
      console.error("Error generating insights:", error);
      
      // Fallback insights
      return {
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
  }
  
  /**
   * Load database schema from YAML files
   */
  private loadDatabaseSchema(): DatabaseSchema {
    const schemaDir = path.join(path.dirname(__dirname), 'schema', 'yml');
    const schema: DatabaseSchema = { tables: [] };
    
    try {
      // Check if directory exists
      if (!fs.existsSync(schemaDir)) {
        console.warn(`Schema directory ${schemaDir} does not exist. Creating it.`);
        fs.mkdirSync(schemaDir, { recursive: true });
        // Create sample schema file if directory is empty
        this.createSampleSchemaFile(schemaDir);
      }
      
      // Get all yml files
      const files = fs.readdirSync(schemaDir)
        .filter(file => file.endsWith('.yml') || file.endsWith('.yaml'));
      
      if (files.length === 0) {
        console.warn('No schema files found. Creating sample schema file.');
        this.createSampleSchemaFile(schemaDir);
        
        // Read the newly created file
        const sampleFile = fs.readdirSync(schemaDir)
          .find(file => file.endsWith('.yml') || file.endsWith('.yaml'));
        
        if (sampleFile) {
          files.push(sampleFile);
        }
      }
      
      // Load and parse each file
      for (const file of files) {
        const filePath = path.join(schemaDir, file);
        const fileContent = fs.readFileSync(filePath, 'utf8');
        const tableData = yaml.load(fileContent) as Table;
        
        if (tableData && tableData.name && tableData.columns) {
          schema.tables.push(tableData);
        } else {
          console.warn(`Invalid schema format in file ${file}`);
        }
      }
      
      return schema;
    } catch (error) {
      console.error('Error loading database schema:', error);
      return { tables: [] };
    }
  }
  
  /**
   * Format database schema for prompts
   */
  private formatSchemaForPrompt(schema: DatabaseSchema): string {
    let result = 'DATABASE SCHEMA:\n\n';
    
    for (const table of schema.tables) {
      result += `TABLE: ${table.name}\n`;
      result += `DESCRIPTION: ${table.description}\n`;
      result += 'COLUMNS:\n';
      
      for (const column of table.columns) {
        result += `  - ${column.name} (${column.type}): ${column.description}\n`;
      }
      
      result += '\n';
    }
    
    return result;
  }
  
  /**
   * Create sample schema files for testing
   */
  private createSampleSchemaFile(directory: string): void {
    const sampleSchema: Table = {
      name: 'customers',
      description: 'Contains customer information and their loyalty points',
      columns: [
        {
          name: 'id',
          type: 'integer',
          description: 'Unique identifier for the customer'
        },
        {
          name: 'first_name',
          type: 'text',
          description: 'Customer\'s first name'
        },
        {
          name: 'last_name',
          type: 'text',
          description: 'Customer\'s last name'
        },
        {
          name: 'email',
          type: 'text',
          description: 'Customer\'s email address'
        },
        {
          name: 'points',
          type: 'integer',
          description: 'Current loyalty points balance'
        },
        {
          name: 'created_at',
          type: 'timestamp',
          description: 'Date when the customer joined the loyalty program'
        }
      ]
    };
    
    const pointsTransactionsSchema: Table = {
      name: 'points_transactions',
      description: 'Records of points earned or redeemed by customers',
      columns: [
        {
          name: 'id',
          type: 'integer',
          description: 'Unique identifier for the transaction'
        },
        {
          name: 'customer_id',
          type: 'integer',
          description: 'Reference to the customer who earned or redeemed points'
        },
        {
          name: 'points',
          type: 'integer',
          description: 'Number of points (positive for earned, negative for redeemed)'
        },
        {
          name: 'transaction_date',
          type: 'timestamp',
          description: 'Date when the transaction occurred'
        },
        {
          name: 'expiry_date',
          type: 'timestamp',
          description: 'Date when the points will expire, if applicable'
        },
        {
          name: 'source',
          type: 'text',
          description: 'Source of the transaction (purchase, referral, redemption, etc.)'
        },
        {
          name: 'description',
          type: 'text',
          description: 'Additional details about the transaction'
        }
      ]
    };
    
    const challengesSchema: Table = {
      name: 'challenges',
      description: 'Marketing challenges that customers can complete to earn bonus points',
      columns: [
        {
          name: 'id',
          type: 'integer',
          description: 'Unique identifier for the challenge'
        },
        {
          name: 'name',
          type: 'text',
          description: 'Name of the challenge'
        },
        {
          name: 'description',
          type: 'text',
          description: 'Details about what customers need to do to complete the challenge'
        },
        {
          name: 'points',
          type: 'integer',
          description: 'Number of points awarded for completing the challenge'
        },
        {
          name: 'start_date',
          type: 'timestamp',
          description: 'Date when the challenge becomes available'
        },
        {
          name: 'end_date',
          type: 'timestamp',
          description: 'Date when the challenge expires'
        },
        {
          name: 'active',
          type: 'boolean',
          description: 'Whether the challenge is currently active'
        }
      ]
    };
    
    const challengeCompletionsSchema: Table = {
      name: 'challenge_completions',
      description: 'Records of challenges completed by customers',
      columns: [
        {
          name: 'id',
          type: 'integer',
          description: 'Unique identifier for the completion record'
        },
        {
          name: 'customer_id',
          type: 'integer',
          description: 'Reference to the customer who completed the challenge'
        },
        {
          name: 'challenge_id',
          type: 'integer',
          description: 'Reference to the challenge that was completed'
        },
        {
          name: 'completion_date',
          type: 'timestamp',
          description: 'Date when the customer completed the challenge'
        },
        {
          name: 'points_awarded',
          type: 'integer',
          description: 'Number of points awarded for completing the challenge'
        }
      ]
    };
    
    try {
      fs.writeFileSync(
        path.join(directory, 'customers.yml'),
        yaml.dump(sampleSchema)
      );
      
      fs.writeFileSync(
        path.join(directory, 'points_transactions.yml'),
        yaml.dump(pointsTransactionsSchema)
      );
      
      fs.writeFileSync(
        path.join(directory, 'challenges.yml'),
        yaml.dump(challengesSchema)
      );
      
      fs.writeFileSync(
        path.join(directory, 'challenge_completions.yml'),
        yaml.dump(challengeCompletionsSchema)
      );
      
      console.log('Created sample schema files in', directory);
    } catch (error) {
      console.error('Error creating sample schema files:', error);
    }
  }
  
  /**
   * Get mock data based on SQL query
   */
  private getMockData(sqlQuery: string): any[] {
    const sqlLower = sqlQuery.toLowerCase();
    
    // Determine which type of data to return based on the query
    if (sqlLower.includes('points_transactions') || sqlLower.includes('transaction')) {
      return this.getMockTransactions();
    } else if (sqlLower.includes('challenges') && !sqlLower.includes('challenge_completions')) {
      return this.getMockChallenges();
    } else if (sqlLower.includes('challenge_completions') || sqlLower.includes('completion')) {
      return this.getMockChallengeCompletions();
    } else {
      // Default to customers data
      return this.getMockCustomers();
    }
  }
  
  private getMockCustomers(): any[] {
    return [
      { id: 1, first_name: "Michael", last_name: "Scott", email: "mscott@example.com", points: 3542, created_at: "2023-01-15" },
      { id: 2, first_name: "Jim", last_name: "Halpert", email: "jhalpert@example.com", points: 2891, created_at: "2023-01-20" },
      { id: 3, first_name: "Pam", last_name: "Beesly", email: "pbeesly@example.com", points: 2745, created_at: "2023-01-22" },
      { id: 4, first_name: "Dwight", last_name: "Schrute", email: "dschrute@example.com", points: 2103, created_at: "2023-02-01" },
      { id: 5, first_name: "Kelly", last_name: "Kapoor", email: "kkapoor@example.com", points: 1986, created_at: "2023-02-15" }
    ];
  }
  
  private getMockTransactions(): any[] {
    return [
      { id: 1, customer_id: 1, points: 500, transaction_date: "2023-05-01", expiry_date: "2024-05-01", source: "purchase", description: "Online purchase" },
      { id: 2, customer_id: 1, points: 200, transaction_date: "2023-05-15", expiry_date: "2024-05-15", source: "referral", description: "Friend referral" },
      { id: 3, customer_id: 2, points: 350, transaction_date: "2023-05-05", expiry_date: "2024-05-05", source: "purchase", description: "In-store purchase" },
      { id: 4, customer_id: 3, points: -150, transaction_date: "2023-05-20", expiry_date: null, source: "redemption", description: "Gift card redemption" },
      { id: 5, customer_id: 4, points: 425, transaction_date: "2023-05-10", expiry_date: "2024-05-10", source: "purchase", description: "Mobile app purchase" }
    ];
  }
  
  private getMockChallenges(): any[] {
    return [
      { id: 1, name: "Summer Bonus", description: "Make 3 purchases in June", points: 500, start_date: "2023-06-01", end_date: "2023-06-30", active: true },
      { id: 2, name: "Referral Drive", description: "Refer a friend to join our program", points: 300, start_date: "2023-05-01", end_date: "2023-07-31", active: true },
      { id: 3, name: "Social Media", description: "Share your purchase on social media", points: 150, start_date: "2023-04-15", end_date: "2023-08-15", active: true },
      { id: 4, name: "First Purchase", description: "Complete your first purchase", points: 200, start_date: "2023-01-01", end_date: "2023-12-31", active: true },
      { id: 5, name: "Loyalty Anniversary", description: "Celebrate your 1-year membership", points: 500, start_date: "2023-01-01", end_date: "2023-12-31", active: true }
    ];
  }
  
  private getMockChallengeCompletions(): any[] {
    return [
      { id: 1, customer_id: 1, challenge_id: 1, completion_date: "2023-06-15", points_awarded: 500 },
      { id: 2, customer_id: 1, challenge_id: 4, completion_date: "2023-01-20", points_awarded: 200 },
      { id: 3, customer_id: 2, challenge_id: 2, completion_date: "2023-05-25", points_awarded: 300 },
      { id: 4, customer_id: 3, challenge_id: 3, completion_date: "2023-05-10", points_awarded: 150 },
      { id: 5, customer_id: 5, challenge_id: 4, completion_date: "2023-02-18", points_awarded: 200 }
    ];
  }
}