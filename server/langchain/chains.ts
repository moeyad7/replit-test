import { ChatOpenAI } from "@langchain/openai";
import { PromptTemplate } from "@langchain/core/prompts";
import { RunnableSequence } from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { formatSchemaForLLM, loadDatabaseSchema, DatabaseSchema } from "../schema/schemaLoader";

/**
 * Creates a chain for generating SQL queries from natural language questions
 */
export function createSqlGenerationChain() {
  // Initialize the LLM
  const llm = new ChatOpenAI({
    modelName: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
    temperature: 0,
  });
  
  // Load database schema
  const schema = loadDatabaseSchema();
  const schemaString = formatSchemaForLLM(schema);
  
  // Create prompt template for SQL generation
  const sqlGenerationPrompt = PromptTemplate.fromTemplate(
    "You are a SQL expert for a loyalty program database. Your task is to convert natural language questions " +
    "into SQL queries that can answer the question.\n\n" +
    "Use the following database schema:\n{schema}\n\n" +
    "Important guidelines:\n" +
    "1. Only use the tables and columns defined in the schema\n" +
    "2. Always use proper SQL syntax for the PostgreSQL dialect\n" +
    "3. Include appropriate JOINs when information from multiple tables is needed\n" +
    "4. Use descriptive aliases for tables (e.g., c for customers, pt for points_transactions)\n" +
    "5. Limit results to 100 rows unless specified otherwise\n" +
    "6. Use simple ORDER BY and GROUP BY clauses when appropriate\n" +
    "7. Format the SQL query nicely with line breaks and proper indentation\n" +
    "8. Only return a valid SQL query and nothing else\n\n" +
    "User question: {question}\n\n" +
    "SQL Query:"
  );
  
  // Create the chain
  const sqlGenerationChain = RunnableSequence.from([
    {
      schema: async () => schemaString,
      question: (input: { question: string }) => input.question,
    },
    sqlGenerationPrompt,
    llm,
    new StringOutputParser(),
  ]);
  
  return sqlGenerationChain;
}

/**
 * Creates a chain for generating insights from query results
 */
export function createInsightsGenerationChain() {
  // Initialize the LLM
  const llm = new ChatOpenAI({
    modelName: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
    temperature: 0.2,
  });
  
  // Create prompt template for insights generation
  const insightsPrompt = PromptTemplate.fromTemplate(`
    You are a business intelligence analyst for a loyalty program. Your task is to analyze the data from a SQL query and provide 
    valuable insights and recommendations.
    
    Original question: {question}
    
    SQL query that was executed: {sqlQuery}
    
    Query results: {results}
    
    Please provide:
    1. A suitable title for this data analysis (keep it short and informative)
    2. 3-5 key insights from the data (focus on patterns, trends, or notable observations)
    3. 2-3 actionable business recommendations based on these insights
    
    Format your response as a JSON object with the following structure (remove the triple backticks):
    ```json
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
    }
    ```
  `);
  
  // Create the chain
  const insightsChain = RunnableSequence.from([
    {
      question: (input: { question: string; sqlQuery: string; results: string }) => input.question,
      sqlQuery: (input: { question: string; sqlQuery: string; results: string }) => input.sqlQuery,
      results: (input: { question: string; sqlQuery: string; results: string }) => input.results
    },
    insightsPrompt,
    llm,
    new StringOutputParser()
  ]);
  
  return insightsChain;
}