import { Request, Response, Router } from 'express';
import { LoyaltyAgent } from './agent';

const router = Router();
const loyaltyAgent = new LoyaltyAgent();

/**
 * POST /api/query
 * Process a natural language query about loyalty program data
 */
router.post('/api/query', async (req: Request, res: Response) => {
  try {
    const { question } = req.body;
    
    if (!question || typeof question !== 'string') {
      return res.status(400).json({
        error: 'A question is required in the request body'
      });
    }
    
    console.log(`Received question: ${question}`);
    
    // Process the question using LangChain agent
    const result = await loyaltyAgent.processQuestion(question);
    
    // Return the results
    return res.status(200).json(result);
  } catch (error: any) {
    console.error('Error processing query:', error);
    return res.status(500).json({
      error: `Failed to process query: ${error?.message || 'Unknown error'}`
    });
  }
});

/**
 * GET /api/schema
 * Get the database schema information
 */
router.get('/api/schema', (req: Request, res: Response) => {
  try {
    // Import schema loader in the route handler to avoid circular dependencies
    const { loadDatabaseSchema } = require('../schema/schemaLoader');
    const schema = loadDatabaseSchema();
    
    return res.status(200).json({
      schema
    });
  } catch (error) {
    console.error('Error loading schema:', error);
    return res.status(500).json({
      error: `Failed to load schema: ${error.message || 'Unknown error'}`
    });
  }
});

export default router;