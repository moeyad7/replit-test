import { pgTable, text, serial, integer, boolean, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Customer table
export const customers = pgTable("customers", {
  id: serial("id").primaryKey(),
  firstName: text("first_name").notNull(),
  lastName: text("last_name").notNull(),
  email: text("email").notNull().unique(),
  status: text("status").notNull().default("active"),
  createdAt: timestamp("created_at").defaultNow(),
});

// Points transactions table
export const pointsTransactions = pgTable("points_transactions", {
  id: serial("id").primaryKey(),
  customerId: integer("customer_id").notNull().references(() => customers.id),
  points: integer("points").notNull(),
  type: text("type").notNull(), // 'earn' or 'redeem'
  category: text("category").notNull(), // 'purchase', 'referral', 'challenge', 'social'
  description: text("description"),
  createdAt: timestamp("created_at").defaultNow(),
});

// Challenges table
export const challenges = pgTable("challenges", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  points: integer("points").notNull(),
  startDate: timestamp("start_date").notNull(),
  endDate: timestamp("end_date").notNull(),
  status: text("status").notNull().default("active"),
});

// Challenge completions table
export const challengeCompletions = pgTable("challenge_completions", {
  id: serial("id").primaryKey(),
  customerId: integer("customer_id").notNull().references(() => customers.id),
  challengeId: integer("challenge_id").notNull().references(() => challenges.id),
  completedAt: timestamp("completed_at").defaultNow(),
  pointsAwarded: integer("points_awarded").notNull(),
});

// Query log table to record user queries and responses
export const queryLogs = pgTable("query_logs", {
  id: serial("id").primaryKey(),
  query: text("query").notNull(),
  sqlQuery: text("sql_query"),
  responseData: text("response_data"),
  createdAt: timestamp("created_at").defaultNow(),
});

// Insert schemas
export const insertCustomerSchema = createInsertSchema(customers).pick({
  firstName: true,
  lastName: true,
  email: true,
  status: true,
});

export const insertPointsTransactionSchema = createInsertSchema(pointsTransactions).pick({
  customerId: true,
  points: true,
  type: true,
  category: true,
  description: true,
});

export const insertChallengeSchema = createInsertSchema(challenges).pick({
  name: true,
  description: true,
  points: true,
  startDate: true,
  endDate: true,
  status: true,
});

export const insertChallengeCompletionSchema = createInsertSchema(challengeCompletions).pick({
  customerId: true,
  challengeId: true,
  pointsAwarded: true,
});

export const insertQueryLogSchema = createInsertSchema(queryLogs).pick({
  query: true,
  sqlQuery: true,
  responseData: true,
});

// Types
export type Customer = typeof customers.$inferSelect;
export type InsertCustomer = z.infer<typeof insertCustomerSchema>;

export type PointsTransaction = typeof pointsTransactions.$inferSelect;
export type InsertPointsTransaction = z.infer<typeof insertPointsTransactionSchema>;

export type Challenge = typeof challenges.$inferSelect;
export type InsertChallenge = z.infer<typeof insertChallengeSchema>;

export type ChallengeCompletion = typeof challengeCompletions.$inferSelect;
export type InsertChallengeCompletion = z.infer<typeof insertChallengeCompletionSchema>;

export type QueryLog = typeof queryLogs.$inferSelect;
export type InsertQueryLog = z.infer<typeof insertQueryLogSchema>;
