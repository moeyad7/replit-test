/**
 * Database Configuration
 * 
 * This file contains configuration settings for the database connection and SQL generation.
 * Modify these settings to match your specific database system.
 */

// SQL dialect configuration
export const sqlDialect = {
  // The SQL dialect to use (mysql, postgresql, sqlserver, etc.)
  type: process.env.SQL_DIALECT || "postgresql",
  
  // String concatenation function
  concatFunction: process.env.SQL_CONCAT_FUNCTION || "CONCAT",
  
  // Date formatting function
  dateFormat: process.env.SQL_DATE_FORMAT || "TO_CHAR",
  
  // Case sensitivity for table and column names
  caseSensitiveIdentifiers: process.env.SQL_CASE_SENSITIVE === "true" || false,
  
  // True if the database requires quotes around identifiers
  quoteIdentifiers: process.env.SQL_QUOTE_IDENTIFIERS === "true" || true,
  
  // Maximum number of results to return in a query by default
  defaultLimit: parseInt(process.env.SQL_DEFAULT_LIMIT || "10"),
};

// OpenAI configuration
export const openAiConfig = {
  // The model to use for SQL generation
  sqlGenerationModel: process.env.OPENAI_SQL_MODEL || "gpt-4o",
  
  // The model to use for insights generation
  insightsModel: process.env.OPENAI_INSIGHTS_MODEL || "gpt-4o",
  
  // Temperature for SQL generation (lower = more deterministic)
  sqlTemperature: parseFloat(process.env.OPENAI_SQL_TEMPERATURE || "0.1"),
  
  // Temperature for insights generation (higher = more creative)
  insightsTemperature: parseFloat(process.env.OPENAI_INSIGHTS_TEMPERATURE || "0.7"),
};

// API configuration
export const apiConfig = {
  // The base URL for the database API
  baseUrl: process.env.DATABASE_API_URL || "https://api.loyalty-database.example.com",
  
  // The API key for authentication
  apiKey: process.env.DATABASE_API_KEY || "your-api-key",
  
  // The timeout for API requests in milliseconds
  timeout: parseInt(process.env.API_TIMEOUT || "30000"),
  
  // Headers to include in API requests
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'Loyalty-Insights-Agent/1.0',
  },
};

// Define examples for each type of query to help with SQL generation
export const queryExamples = {
  customerPoints: {
    question: "Show me the top 5 customers with the most points",
    sql: `SELECT 
  c.id,
  ${sqlDialect.concatFunction}(c.first_name, ' ', c.last_name) AS customer_name,
  c.email,
  SUM(pt.points) AS total_points
FROM 
  customers c
JOIN 
  points_transactions pt ON c.id = pt.customer_id
WHERE 
  pt.type = 'earn'
GROUP BY 
  c.id, c.first_name, c.last_name, c.email
ORDER BY 
  total_points DESC
LIMIT 5`
  },
  expiringPoints: {
    question: "Which customers have points expiring soon?",
    sql: `SELECT 
  c.id, 
  ${sqlDialect.concatFunction}(c.first_name, ' ', c.last_name) AS customer_name,
  c.email,
  SUM(pt.points) AS expiring_points,
  ${sqlDialect.dateFormat}(pt.created_at + INTERVAL '1 year', 'YYYY-MM-DD') AS expiry_date
FROM 
  customers c
JOIN 
  points_transactions pt ON c.id = pt.customer_id
WHERE 
  pt.type = 'earn' 
  AND pt.created_at BETWEEN NOW() - INTERVAL '1 year' AND NOW() - INTERVAL '11 months'
GROUP BY 
  c.id, c.first_name, c.last_name, c.email, pt.created_at
ORDER BY 
  pt.created_at ASC
LIMIT ${sqlDialect.defaultLimit}`
  },
  challengeCompletions: {
    question: "What are the completion rates for our challenges?",
    sql: `SELECT 
  ch.id,
  ch.name AS challenge_name,
  COUNT(cc.id) AS completions,
  (SELECT COUNT(DISTINCT customer_id) FROM challenge_completions) AS total_participants,
  ROUND((COUNT(cc.id) * 100.0 / NULLIF((SELECT COUNT(DISTINCT customer_id) FROM challenge_completions), 0)), 1) AS completion_rate
FROM 
  challenges ch
LEFT JOIN 
  challenge_completions cc ON ch.id = cc.challenge_id
GROUP BY 
  ch.id, ch.name
ORDER BY 
  completions DESC
LIMIT ${sqlDialect.defaultLimit}`
  }
};