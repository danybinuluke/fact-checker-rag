// Backend API types matching Pydantic models

export interface ClaimModel {
  claim: string;
  entities: string[];
  confidence: number;
  source_doc?: string;
}

export interface ExtractClaimsResponse {
  status: string;
  document: string;
  claims: ClaimModel[];
  timestamp: string;
}

export interface VerifyClaimResponse {
  status: string;
  user_claim: string;
  verification_status: 'SUPPORT' | 'CONTRADICTION' | 'NEUTRAL';
  confidence_score: number;
  corpus_confidence?: number;
  training_confidence?: number;
  source?: 'corpus' | 'training' | 'both' | 'unknown';
  corpus_match_found?: boolean;
  corpus_match_score?: number;
  explanation: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  response_time_ms: number;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  primary_llm: string;
  fallback_llm: string;
  available_models: string[];
  services: Record<string, string>;
}

export interface GraphNode {
  id: string;
  label: string;
  confidence: number;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string; // "supports", "contradicts", "neutral_to"
  weight: number;
}

export interface GraphDataResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface MetricsResponse {
  performance: {
    total_requests: number;
    extraction_count: number;
    verification_count: number;
    errors_total: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
    uptime_seconds: number;
    corpus_vectors: number;
  };
  models: {
    primary: string;
    fallback: string;
    ollama_available: boolean;
    embedding_model: string;
  };
  system_info: {
    environment: string;
    python_version: string;
    vector_store: string;
    graph_store: string;
  };
}
