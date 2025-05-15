# SQL Query REST API Setup Guide

This application is designed to send SQL queries to a REST API endpoint and process the results. This guide explains how to set up the API endpoint.

## API Requirements

### 1. Query Execution Endpoint

Your REST API should provide an endpoint that accepts SQL queries and returns the results:

- **URL**: `/execute-query` (can be customized in `server/config.ts`)
- **Method**: POST
- **Headers**:
  - `Content-Type`: `application/json`
  - `Authorization`: `Bearer YOUR_API_KEY` (if needed)
  - Any additional headers from `apiConfig.headers` in `server/config.ts`

- **Request Body**:
  ```json
  {
    "sql": "SELECT * FROM customers LIMIT 10",
    "format": "json",
    "maxRows": 10
  }
  ```

- **Response Format**: JSON array of objects representing the query results
  ```json
  [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "points": 1500
    },
    {
      "id": 2,
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@example.com",
      "points": 2300
    }
  ]
  ```

### 2. Schema Endpoint (Optional)

If you have a schema endpoint that returns the structure of your database, the application can use this to generate more accurate SQL queries:

- **URL**: `/schema`
- **Method**: GET
- **Response Format**: JSON with the following structure:
  ```json
  {
    "tables": [
      {
        "name": "customers",
        "description": "Customer information",
        "columns": [
          {
            "name": "id",
            "type": "integer",
            "description": "Unique customer identifier"
          },
          {
            "name": "first_name",
            "type": "text",
            "description": "Customer's first name"
          }
        ]
      }
    ]
  }
  ```

## Configuration

1. Update the `.env` file with your API endpoint and key:
   ```
   DATABASE_API_URL=https://your-api-endpoint.com
   DATABASE_API_KEY=your_api_key_here
   ```

2. Configure request parameters in `server/config.ts`:
   ```typescript
   export const apiConfig = {
     baseUrl: process.env.DATABASE_API_URL || "https://your-api-endpoint.com",
     apiKey: process.env.DATABASE_API_KEY || "your-api-key",
     timeout: parseInt(process.env.API_TIMEOUT || "30000"),
     headers: {
       'Content-Type': 'application/json',
       'User-Agent': 'Loyalty-Insights-Agent/1.0',
       // Add any additional headers your API requires
     },
   };
   ```

## Customizing the Request Format

If your API expects a different format than the default, you can customize it in `server/queryService.ts`:

```typescript
async executeQuery(sqlQuery: string) {
  try {
    const response = await axios.post(
      `${this.apiBaseUrl}/execute-query`,
      { 
        // Customize this object to match your API's expected request format
        sql: sqlQuery,            // The SQL query to execute
        format: "json",           // Response format
        maxRows: 100,             // Maximum rows to return
        includeMetadata: true,    // Additional parameters as needed
        parameters: []            // Query parameters if needed
      },
      {
        headers: this.headers,
        timeout: this.timeout
      }
    );
    
    // Process the response if needed
    return response.data;
  } catch (error) {
    // Error handling...
  }
}
```

## Testing Your API Connection

You can test your API connection by running:

```bash
curl -X POST https://your-api-endpoint.com/execute-query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{
    "sql": "SELECT * FROM customers LIMIT 1",
    "format": "json"
  }'
```

This should return data in the format your API provides.