import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { generateSQL, analyzeQueryResults } from "./openai";
import { queryService } from "./queryService";
import { LoyaltyAgent } from './langchain/simplified';

export async function registerRoutes(app: Express): Promise<Server> {
  // Initialize LangChain LoyaltyAgent
  const loyaltyAgent = new LoyaltyAgent();
  
  // API route for executing queries (using LangChain agent)
  app.post("/api/query", async (req, res) => {
    try {
      const { query } = req.body;
      
      if (!query) {
        return res.status(400).json({ message: "Query is required" });
      }
      
      console.log(`Processing query with LangChain agent: ${query}`);
      
      // Use the LangChain LoyaltyAgent to process the query
      const result = await loyaltyAgent.processQuestion(query);
      
      // Return the complete response from the LangChain agent
      res.json(result);
      
    } catch (error: any) {
      console.error("Error processing query:", error);
      res.status(500).json({ 
        message: "Error processing query",
        error: error?.message || 'Unknown error'
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
