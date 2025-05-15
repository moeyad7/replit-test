# Database API Integration Setup Guide

This application connects to your loyalty program database API to retrieve and analyze customer data. Follow these steps to connect it to your database system.

## Environment Variables Setup

1. Create a `.env` file in the root directory of the project (copy from `.env.example`)
2. Add your API credentials:
   ```
   DATABASE_API_URL=https://your-loyalty-database-api-url.com
   DATABASE_API_KEY=your_database_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## API Requirements

Your database API should provide the following endpoints:

### 1. Schema Endpoint

- **URL**: `/schema`
- **Method**: GET
- **Authorization**: Bearer token authentication with your API key
- **Response Format**: JSON with the following structure:

```json
{
  "tables": [
    {
      "name": "table_name",
      "description": "Description of the table",
      "columns": [
        {
          "name": "column_name",
          "type": "data_type",
          "description": "Description of the column"
        },
        // More columns...
      ]
    },
    // More tables...
  ]
}
```

### 2. Query Execution Endpoint

- **URL**: `/execute-query`
- **Method**: POST
- **Authorization**: Bearer token authentication with your API key
- **Request Body**:
  ```json
  {
    "query": "SQL query string here"
  }
  ```
- **Response Format**: JSON array of objects representing the query results

## Customizing SQL Generation for Your Schema

You can customize the SQL generation prompts in `server/openai.ts` to match your specific database requirements:

1. Adjust SQL dialect by updating the system prompt in the `generateSQL` function
2. Add specific formatting requirements for your database system
3. Include any database-specific functions or syntax that should be used

## Fallback Mechanism

The application includes a fallback mechanism that uses mock data when API connection fails. This allows for development and testing without an active API connection.

To disable the fallback and require a valid API connection:

1. Update the `executeQuery` method in `server/queryService.ts`
2. Remove the mock data fallback code in the catch block
3. Return a proper error to the client instead

## Custom Schema Modifications

If your database schema differs significantly from the expected loyalty program structure:

1. Update the fallback schema in the `getDatabaseSchema` method to match your actual schema structure
2. Modify mock data generators to return data that matches your schema format
3. Adjust the SQL generation prompts to generate queries compatible with your schema