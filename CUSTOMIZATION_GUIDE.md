# AI Loyalty Program Customization Guide

This guide explains how to customize the AI model instructions, SQL generation, and database connectivity to work with your specific loyalty program schema and requirements.

## Table of Contents
1. [Model Customization](#model-customization)
2. [SQL Dialect Configuration](#sql-dialect-configuration)
3. [API Connection Setup](#api-connection-setup)
4. [Query Examples](#query-examples)
5. [OpenAI Models and Parameters](#openai-models-and-parameters)
6. [Fallback Mechanism](#fallback-mechanism)

## Model Customization

The AI models in this application are designed to be customized for your specific needs. The main customization points are:

### 1. SQL Generation Prompt

The SQL generation prompt is located in `server/openai.ts` in the `generateSQL` function. You can modify this prompt to:

- Add specific instructions for your database schema
- Include additional SQL formatting requirements
- Specify custom joins or relationships
- Add business rules or constraints

For example, if your database has specific naming conventions or important relationships between tables, you can add this information to the prompt.

### 2. Analysis Prompt

The analysis prompt is also in `server/openai.ts` in the `analyzeQueryResults` function. Customize this to:

- Focus on specific KPIs relevant to your loyalty program
- Provide industry benchmarks or standards
- Include your company's voice and tone
- Add specific recommendation types tailored to your business

## SQL Dialect Configuration

Configure your SQL dialect settings in `server/config.ts`. The `sqlDialect` object lets you specify:

```typescript
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
```

You can set these values through environment variables or directly in the config file.

### Common SQL Dialect Settings

#### MySQL
```
SQL_DIALECT=mysql
SQL_CONCAT_FUNCTION=CONCAT
SQL_DATE_FORMAT=DATE_FORMAT
SQL_CASE_SENSITIVE=false
SQL_QUOTE_IDENTIFIERS=true
```

#### PostgreSQL
```
SQL_DIALECT=postgresql
SQL_CONCAT_FUNCTION=CONCAT
SQL_DATE_FORMAT=TO_CHAR
SQL_CASE_SENSITIVE=false
SQL_QUOTE_IDENTIFIERS=true
```

#### SQL Server
```
SQL_DIALECT=sqlserver
SQL_CONCAT_FUNCTION=CONCAT
SQL_DATE_FORMAT=FORMAT
SQL_CASE_SENSITIVE=false
SQL_QUOTE_IDENTIFIERS=true
```

## API Connection Setup

To connect the application to your database API, configure the following in `.env`:

```
DATABASE_API_URL=https://your-loyalty-database-api-url.com
DATABASE_API_KEY=your_database_api_key_here
```

Your API should implement two key endpoints:

1. **Schema Endpoint** (`GET /schema`): Returns the database schema as described in DATABASE_API_SETUP.md
2. **Query Execution Endpoint** (`POST /execute-query`): Executes SQL queries and returns results

## Query Examples

The application includes query examples in `server/config.ts` that help guide the AI in generating appropriate SQL for your schema. Customize these examples to better match your specific schema and common query patterns:

```typescript
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
  // Add more examples here...
};
```

## OpenAI Models and Parameters

Configure the OpenAI models and parameters in `server/config.ts`:

```typescript
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
```

For SQL generation, a lower temperature (0.1-0.3) is recommended for more consistent and accurate results. For insights and recommendations, a higher temperature (0.7-0.9) encourages more creative and diverse responses.

## Fallback Mechanism

The application includes a fallback mechanism that provides mock responses when API connections fail. This allows the application to be used for demonstrations or testing without a live database connection.

You can customize the mock responses in the `getMockTopPointsEarners`, `getMockExpiringPoints`, and `getMockChallengeCompletions` functions in `server/queryService.ts`.

To disable the fallback mechanism entirely and require a valid API connection:

1. Modify the `executeQuery` method in `server/queryService.ts`
2. Replace the mock data fallback with an appropriate error response
3. Update the client-side error handling to notify users when the database connection fails

This will ensure that the application only operates with real data from your database.