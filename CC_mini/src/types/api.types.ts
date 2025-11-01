// Authentication Types
export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  email: string;
  created_at: string;
}

export interface LoginRequest {
  username: string; // Actually email, but backend expects 'username' field
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface UserResponse {
  email: string;
  created_at: string;
}

// Document Types
export interface UploadResponse {
  message: string;
  document_id: string;
  filename: string;
  status: ProcessingStatus;
}

export type ProcessingStatus = 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface Document {
  _id: string;
  user_id: string;
  original_filename: string;
  local_path: string;
  processing_status: ProcessingStatus;
  uploaded_at: string;
}

// Generated Content Types
export type ContentType = 'SUMMARY' | 'MINDMAP' | 'FLASHCARDS';

export interface GeneratedContent {
  _id: string;
  document_id: string;
  user_id: string;
  content_type: ContentType;
  content_data: SummaryData | MindMapData | FlashcardsData;
  created_at: string;
}

export interface SummaryData {
  summary: string;
}

export interface MindMapData {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

export interface MindMapNode {
  id: string;
  label: string;
  level: number;
  parent?: string;
}

export interface MindMapEdge {
  from: string;
  to: string;
}

export interface FlashcardsData {
  flashcards: Flashcard[];
}

export interface Flashcard {
  question: string;
  answer: string;
}

// Chat Types
export interface ChatRequest {
  query: string;
  document_ids: string[];
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export interface Source {
  document_id: string;
  page: number;
  score?: number;
}

// Message Type for chat history
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

// Error Types
export interface ApiError {
  detail: string | { msg: string; type: string }[];
}
