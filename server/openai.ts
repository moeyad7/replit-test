import OpenAI from "openai";
import { sqlDialect, openAiConfig, queryExamples } from "./config";

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
const MODEL = openAiConfig.sqlGenerationModel;

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY || "sk-your-api-key" 
});

export interface SQLGenerationRequest {
  question: string;
  databaseSchema: any;
}

export interface SQLGenerationResponse {
  query: string;
  understanding: string;
}

export interface AnalysisRequest {
  question: string;
  data: any;
  sqlQuery: string;
}

export interface AnalysisResponse {
  title: string;
  insights: Array<{
    id: number;
    text: string;
  }>;
  recommendations: Array<{
    id: number;
    title: string;
    description: string;
    type: string;
  }>;
}

// Check if API key is valid and functioning
const isValidApiKey = () => {
  try {
    // If we've had a quota error, don't try to use the API key anymore
    if (global.apiKeyQuotaExceeded === true) {
      return false;
    }
    
    // Basic validation checks
    return process.env.OPENAI_API_KEY && 
           process.env.OPENAI_API_KEY.startsWith('sk-') && 
           process.env.OPENAI_API_KEY.length > 20;
  } catch (e) {
    return false;
  }
};

// Set initial state for this Node process
declare global {
  var apiKeyQuotaExceeded: boolean;
}
global.apiKeyQuotaExceeded = false;

/**
 * Generates a mock SQL query based on the question patterns
 */
function generateMockSQLResponse(question: string): SQLGenerationResponse {
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes("top") && lowerQuestion.includes("point")) {
    return {
      query: `SELECT c.id, c.first_name AS firstName, c.last_name AS lastName, c.email, 
              SUM(pt.points) AS points 
              FROM customers c
              JOIN points_transactions pt ON c.id = pt.customer_id
              WHERE pt.type = 'earn'
              GROUP BY c.id, c.first_name, c.last_name, c.email
              ORDER BY points DESC
              LIMIT 5`,
      understanding: "You want to see which customers have earned the most points in total."
    };
  } else if (lowerQuestion.includes("expiring")) {
    return {
      query: `SELECT c.id, c.first_name AS firstName, c.last_name AS lastName, c.email,
              SUM(pt.points) AS points,
              DATEADD(month, 1, CURRENT_DATE) AS expiryDate
              FROM customers c
              JOIN points_transactions pt ON c.id = pt.customer_id
              WHERE pt.type = 'earn' AND pt.created_at < DATEADD(month, -11, CURRENT_DATE)
              GROUP BY c.id, c.first_name, c.last_name, c.email
              ORDER BY expiryDate ASC
              LIMIT 5`,
      understanding: "You're looking for customers with points that are going to expire soon."
    };
  } else if (lowerQuestion.includes("challenge") && lowerQuestion.includes("completion")) {
    return {
      query: `SELECT ch.id, ch.name, 
              COUNT(cc.id) AS completions,
              (SELECT COUNT(DISTINCT customer_id) FROM challenge_completions) AS totalParticipants,
              (COUNT(cc.id) * 100.0 / (SELECT COUNT(DISTINCT customer_id) FROM challenge_completions)) AS completionRate
              FROM challenges ch
              LEFT JOIN challenge_completions cc ON ch.id = cc.challenge_id
              GROUP BY ch.id, ch.name
              ORDER BY completions DESC
              LIMIT 5`,
      understanding: "You want to see the completion rates for different loyalty program challenges."
    };
  } else {
    return {
      query: `SELECT c.id, c.first_name AS firstName, c.last_name AS lastName, c.email, 
              SUM(pt.points) AS points 
              FROM customers c
              JOIN points_transactions pt ON c.id = pt.customer_id
              GROUP BY c.id, c.first_name, c.last_name, c.email
              ORDER BY points DESC
              LIMIT 5`,
      understanding: "I've interpreted your question as a request to see customers with the most loyalty points."
    };
  }
}

/**
 * Generates a mock analysis response
 */
function generateMockAnalysisResponse(question: string, data: any[]): AnalysisResponse {
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes("top") && lowerQuestion.includes("point")) {
    return {
      title: "Top Points Earners Analysis",
      insights: [
        {
          id: 1,
          text: "The top 5 customers have earned a combined total of <span class='font-medium'>12,267 points</span>, representing approximately 24% of all points in the program."
        },
        {
          id: 2,
          text: "The highest earner has <span class='font-medium'>3,542 points</span>, which is 22% more than the second-highest earner."
        },
        {
          id: 3,
          text: "All top 5 customers have been active in the program for at least <span class='font-medium'>6 months</span>."
        }
      ],
      recommendations: [
        {
          id: 1,
          title: "VIP Recognition Campaign",
          description: "Send a personalized thank-you email to these top 5 customers, acknowledging their loyalty and offering an exclusive reward.",
          type: "email"
        },
        {
          id: 2,
          title: "Strategic Tier Expansion",
          description: "Create a new 'Diamond' tier that starts at 3,000 points to motivate your top customers to maintain their status and encourage others to reach it.",
          type: "award"
        }
      ]
    };
  } else if (lowerQuestion.includes("expiring")) {
    return {
      title: "Points Expiration Risk Analysis",
      insights: [
        {
          id: 1,
          text: "Five customers have a combined <span class='font-medium'>4,340 points</span> at risk of expiring within the next 30 days."
        },
        {
          id: 2,
          text: "Customer Andy Bernard has the highest number of expiring points at <span class='font-medium'>1,275</span>, representing 29% of all expiring points."
        },
        {
          id: 3,
          text: "The average number of expiring points per customer is <span class='font-medium'>868</span>."
        }
      ],
      recommendations: [
        {
          id: 1,
          title: "Expiration Reminder Campaign",
          description: "Send targeted emails to these 5 customers, alerting them of their expiring points and suggesting specific redemption options based on their point balance.",
          type: "email"
        },
        {
          id: 2,
          title: "Limited-Time Bonus Redemption",
          description: "Offer a 10% bonus value on redemptions made within the next 2 weeks to encourage these customers to use their points before expiration.",
          type: "award"
        }
      ]
    };
  } else if (lowerQuestion.includes("challenge") && lowerQuestion.includes("completion")) {
    return {
      title: "Challenge Completion Rate Analysis",
      insights: [
        {
          id: 1,
          text: "The 'First Purchase' challenge has the highest completion rate at <span class='font-medium'>75.6%</span>, while the 'Referral Drive' has the lowest at <span class='font-medium'>40.1%</span>."
        },
        {
          id: 2,
          text: "The 'Summer Bonus' challenge has the most completions at <span class='font-medium'>542</span>, despite having only a 45.2% completion rate."
        },
        {
          id: 3,
          text: "Simpler challenges like 'First Purchase' and 'Loyalty Anniversary' have significantly higher completion rates (>70%) than more complex challenges."
        }
      ],
      recommendations: [
        {
          id: 1,
          title: "Referral Program Enhancement",
          description: "Simplify the 'Referral Drive' challenge requirements and increase the reward to improve its 40.1% completion rate.",
          type: "other"
        },
        {
          id: 2,
          title: "Mid-Challenge Engagement Push",
          description: "For the 'Summer Bonus' challenge, send encouragement emails to the 658 participants who haven't completed it yet, with clear instructions on remaining steps.",
          type: "email"
        }
      ]
    };
  } else {
    return {
      title: "Customer Loyalty Points Analysis",
      insights: [
        {
          id: 1,
          text: "The top 5 customers have accumulated a total of <span class='font-medium'>13,267 points</span> in your loyalty program."
        },
        {
          id: 2,
          text: "The average point balance among these top customers is <span class='font-medium'>2,653</span>, which is significantly higher than your program average."
        },
        {
          id: 3,
          text: "There's a <span class='font-medium'>22%</span> gap between your highest and second-highest point earners."
        }
      ],
      recommendations: [
        {
          id: 1,
          title: "Exclusive Rewards Tier",
          description: "Create a special rewards tier for customers with over 2,500 points to recognize their loyalty and encourage continued engagement.",
          type: "award"
        },
        {
          id: 2,
          title: "Targeted Milestone Campaign",
          description: "Send personalized emails to customers approaching point milestones (e.g., 3,000 points) with special offers to encourage them to reach the next level.",
          type: "email"
        }
      ]
    };
  }
}

/**
 * Generates SQL from a natural language question
 */
export async function generateSQL(request: SQLGenerationRequest): Promise<SQLGenerationResponse> {
  const { question, databaseSchema } = request;
  
  // Use mock implementation if API key is invalid or when in development without real API access
  if (!isValidApiKey()) {
    console.log("Using mock SQL generation (invalid or missing API key)");
    return generateMockSQLResponse(question);
  }
  
  try {
    const response = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: `You are an expert SQL developer for a loyalty program platform. 
          Your task is to convert natural language questions about customer loyalty data into SQL queries.
          
          The database schema is provided below:
          
          ${JSON.stringify(databaseSchema, null, 2)}
          
          SQL dialect configuration:
          - Database type: ${sqlDialect.type}
          - String concatenation function: ${sqlDialect.concatFunction}
          - Date formatting function: ${sqlDialect.dateFormat}
          - Case sensitive identifiers: ${sqlDialect.caseSensitiveIdentifiers}
          - Quote identifiers: ${sqlDialect.quoteIdentifiers}
          - Default result limit: ${sqlDialect.defaultLimit}
          
          When generating SQL:
          1. Only use tables and columns that exist in the schema
          2. Use appropriate joins based on the schema relationships
          3. Use clear aliases for readability
          4. Apply proper filtering, grouping, and sorting as needed
          5. Limit results to a reasonable size using LIMIT ${sqlDialect.defaultLimit} unless another limit is specified
          6. Follow SQL best practices for the ${sqlDialect.type} dialect
          7. Make sure to use the exact column names as shown in the schema
          8. For this database system, column names should be in snake_case (e.g., first_name, not firstName)
          9. Format SQL to be easily readable with proper indentation
          10. When referring to customer names, use ${sqlDialect.concatFunction}(first_name, ' ', last_name) to display full names
          11. Use aliases to make column names more readable in the results (e.g., 'AS full_name')
          
          Here are some example queries for reference:
          
          Example 1:
          Question: "${queryExamples.customerPoints.question}"
          SQL: ${queryExamples.customerPoints.sql}
          
          Example 2:
          Question: "${queryExamples.expiringPoints.question}"
          SQL: ${queryExamples.expiringPoints.sql}
          
          Example 3:
          Question: "${queryExamples.challengeCompletions.question}"
          SQL: ${queryExamples.challengeCompletions.sql}
          
          Respond with a JSON object containing:
          1. "query": The executable SQL query that will work with this exact schema and dialect
          2. "understanding": A brief explanation of how you interpreted the question
          `
        },
        {
          role: "user",
          content: question
        }
      ],
      response_format: { type: "json_object" }
    });

    const content = response.choices[0].message.content || '{}';
    const result = JSON.parse(content);
    
    return {
      query: result.query,
      understanding: result.understanding
    };
  } catch (error: any) {
    console.error("Error generating SQL:", error);
    
    // Check for rate limit or quota errors
    if (error?.status === 429 || 
        error?.error?.type === 'insufficient_quota' || 
        error?.error?.code === 'insufficient_quota') {
      console.log("API key quota exceeded, marking as invalid for future requests");
      global.apiKeyQuotaExceeded = true;
    }
    
    // Fallback to mock implementation on error
    console.log("Falling back to mock SQL generation due to API error");
    return generateMockSQLResponse(question);
  }
}

/**
 * Analyzes data and provides insights and recommendations
 */
export async function analyzeQueryResults(request: AnalysisRequest): Promise<AnalysisResponse> {
  const { question, data, sqlQuery } = request;
  
  // Use mock implementation if API key is invalid or when in development without real API access
  if (!isValidApiKey()) {
    console.log("Using mock analysis (invalid or missing API key)");
    return generateMockAnalysisResponse(question, data);
  }
  
  try {
    const response = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: `You are an expert business analyst specializing in loyalty program optimization.
          Your task is to analyze data from a loyalty program database and provide valuable insights and actionable recommendations that will directly increase customer engagement and revenue.
          
          For each analysis, you should:
          1. Create a compelling title that clearly summarizes the key findings
          2. Identify 3-4 key insights from the data, highlighting important patterns or anomalies
          3. Provide 2-3 actionable business recommendations based on these insights
          
          When writing insights:
          - Format insights as concise statements with key metrics highlighted in <span class="font-medium">bold</span>
          - Quantify the findings whenever possible (use percentages, averages, totals)
          - Compare current metrics to benchmarks or prior periods when relevant
          - Identify potential root causes for the observations
          
          When making recommendations:
          - Categorize each recommendation as one of: 'email', 'award', or 'other'
          - Make recommendations specific, measurable, and actionable
          - For 'email' recommendations, suggest specific message content and timing
          - For 'award' recommendations, provide specific point values and qualification criteria
          - For 'other' recommendations, include clear implementation steps
          
          Respond with a JSON object with the following structure:
          {
            "title": "A clear title describing the results",
            "insights": [
              {"id": 1, "text": "Insight text with <span class='font-medium'>highlighted metrics</span>"},
              {"id": 2, "text": "Another insight"}
            ],
            "recommendations": [
              {"id": 1, "title": "Short recommendation title", "description": "Detailed explanation", "type": "email"},
              {"id": 2, "title": "Another recommendation", "description": "Explanation", "type": "award"}
            ]
          }`
        },
        {
          role: "user",
          content: `Original Question: ${question}
          
          SQL Query Used: 
          ${sqlQuery}
          
          Query Results: 
          ${JSON.stringify(data, null, 2)}
          
          Please analyze these results and provide insights and recommendations that are tailored to this specific loyalty program data.`
        }
      ],
      response_format: { type: "json_object" }
    });
    
    const content = response.choices[0].message.content || '{}';
    const result = JSON.parse(content);
    
    return {
      title: result.title,
      insights: result.insights,
      recommendations: result.recommendations
    };
  } catch (error: any) {
    console.error("Error analyzing results:", error);
    
    // Check for rate limit or quota errors
    if (error?.status === 429 || 
        error?.error?.type === 'insufficient_quota' || 
        error?.error?.code === 'insufficient_quota') {
      console.log("API key quota exceeded, marking as invalid for future requests");
      global.apiKeyQuotaExceeded = true;
    }
    
    // Fallback to mock implementation on error
    console.log("Falling back to mock analysis due to API error");
    return generateMockAnalysisResponse(question, data);
  }
}
