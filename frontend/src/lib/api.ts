import axios, { AxiosInstance } from 'axios';
import {
  ExtractClaimsResponse,
  VerifyClaimResponse,
  HealthResponse,
  GraphDataResponse,
  MetricsResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class FactCheckerAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
    });
  }

  async extractClaims(text: string, documentId?: string): Promise<ExtractClaimsResponse> {
    try {
      const response = await this.client.post('/extract-claims', {
        text,
        document_id: documentId || undefined,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async uploadDocument(file: File): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await this.client.post('/upload-document', formData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async verifyClaim(claim: string, model?: string): Promise<VerifyClaimResponse> {
    try {
      const response = await this.client.post('/verify-claim', {
        claim,
        model,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getGraphData(): Promise<GraphDataResponse> {
    try {
      const response = await this.client.get('/graph-data');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getMetrics(): Promise<MetricsResponse> {
    try {
      const response = await this.client.get('/metrics');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      let message = error.message || 'API request failed';
      const detail = error.response?.data?.detail;
      if (detail) {
        if (typeof detail === 'string') {
          message = detail;
        } else if (Array.isArray(detail) || typeof detail === 'object') {
          message = JSON.stringify(detail);
        }
      }
      return new Error(message);
    }
    return error instanceof Error ? error : new Error('Unknown error occurred');
  }
}

export const api = new FactCheckerAPI();
