import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface TableColumn {
  name: string;
  type: string;
  description: string;
}

export interface Table {
  name: string;
  description: string;
  columns: TableColumn[];
}

export interface DatabaseSchema {
  tables: Table[];
}

/**
 * Loads database schema from YAML files in the schema directory
 */
export function loadDatabaseSchema(): DatabaseSchema {
  const schemaDir = path.join(__dirname, 'yml');
  const schema: DatabaseSchema = { tables: [] };
  
  try {
    // Check if directory exists
    if (!fs.existsSync(schemaDir)) {
      console.warn(`Schema directory ${schemaDir} does not exist. Creating it.`);
      fs.mkdirSync(schemaDir, { recursive: true });
      // Create sample schema file if directory is empty
      createSampleSchemaFile(schemaDir);
    }
    
    // Get all yml files
    const files = fs.readdirSync(schemaDir)
      .filter(file => file.endsWith('.yml') || file.endsWith('.yaml'));
    
    if (files.length === 0) {
      console.warn('No schema files found. Creating sample schema file.');
      createSampleSchemaFile(schemaDir);
      
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
 * Creates a sample schema file for the loyalty program database
 */
function createSampleSchemaFile(directory: string): void {
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
 * Convert database schema to string format for LLM prompts
 */
export function formatSchemaForLLM(schema: DatabaseSchema): string {
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