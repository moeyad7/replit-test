import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { generateSQL, analyzeQueryResults } from "./openai";
import { queryService } from "./queryService";

export async function registerRoutes(app: Express): Promise<Server> {
  // API route for executing queries
  app.post("/api/query", async (req, res) => {
    try {
      const { query } = req.body;
      
      if (!query) {
        return res.status(400).json({ message: "Query is required" });
      }
      
      // Get database schema
      const dbSchema = await queryService.getDatabaseSchema();
      
      // Step 1: Generate SQL from natural language question
      const sqlGeneration = await generateSQL({
        question: query,
        databaseSchema: dbSchema
      });
      
      // Step 2: Execute SQL query against database
      const startTime = Date.now();
      const queryResults = await queryService.executeQuery(sqlGeneration.query);
      const queryTime = ((Date.now() - startTime) / 1000).toFixed(2);
      
      // Step 3: Analyze results
      const analysis = await analyzeQueryResults({
        question: query,
        data: queryResults,
        sqlQuery: sqlGeneration.query
      });
      
      // Step 4: Return the complete response
      res.json({
        queryUnderstanding: sqlGeneration.understanding,
        sqlQuery: sqlGeneration.query,
        databaseResults: {
          count: queryResults.length,
          time: parseFloat(queryTime)
        },
        title: analysis.title,
        data: queryResults,
        insights: analysis.insights,
        recommendations: analysis.recommendations
      });
    } catch (error: any) {
      console.error("Error processing query:", error);
      res.status(500).json({ 
        message: "Error processing query",
        error: error.message
      });
    }
  });

  // API route for getting database schema
  app.get("/api/schema", async (req, res) => {
    try {
      const schema = await queryService.getDatabaseSchema();
      res.json(schema);
    } catch (error: any) {
      console.error("Error retrieving schema:", error);
      res.status(500).json({ 
        message: "Error retrieving database schema",
        error: error.message
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
