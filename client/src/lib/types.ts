export interface Customer {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  points: number;
}

export interface Insight {
  id: number;
  text: string;
}

export interface Recommendation {
  id: number;
  title: string;
  description: string;
  type: 'email' | 'award' | 'other';
}

export interface DatabaseResults {
  count: number;
  time: number;
}

export interface QueryResponse {
  queryUnderstanding: string;
  sqlQuery: string;
  databaseResults: DatabaseResults;
  title: string;
  data: Customer[];
  insights: Insight[];
  recommendations: Recommendation[];
}

// Database schema types
export interface DbSchema {
  tables: DbTable[];
}

export interface DbTable {
  name: string;
  description: string;
  columns: DbColumn[];
}

export interface DbColumn {
  name: string;
  type: string;
  description: string;
}
