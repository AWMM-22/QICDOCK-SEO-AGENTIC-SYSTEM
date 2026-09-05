import axios from 'axios';
import type {
  CreatePlanRequest, CreatePlanResponse, PlanResponse, CalendarResponse,
  DayRecommendationResponse, RegenerateRequest,
  RegenerateResponse, ImageGenerateRequest, ImageGenerateResponse,
  BrandKnowledgeUpdateRequest, BrandKnowledgeUpdateResponse,
  HealthResponse, PlanJobsResponse
} from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthApi = {
  check: () => api.get<HealthResponse>('/health'),
};

export const projectApi = {
  create: (name: string) => api.post<{ project_id: number; name: string }>('/projects', { name }),
  list: () => api.get<{ id: number; name: string; created_at: string }[]>('/projects'),
};

export const planApi = {
  create: (projectId: number, data: CreatePlanRequest) => 
    api.post<CreatePlanResponse>(`/projects/${projectId}/plans`, data),
  listAll: () => api.get<PlanResponse[]>('/plans'),
  getLatest: () => api.get<PlanResponse>('/latest-plan'),
  get: (planId: number) => api.get<PlanResponse>(`/plans/${planId}`),
  getCalendar: (planId: number) => api.get<CalendarResponse>(`/plans/${planId}/calendar`),
  getUnifiedCalendar: (startDate?: string, endDate?: string) => 
    api.get<CalendarResponse>('/calendar', { params: { start_date: startDate, end_date: endDate } }),
  getDayRecommendation: (planId: number, date: string, platform?: string) => 
    api.get<DayRecommendationResponse>(`/plans/${planId}/entries/${date}`, { params: { platform } }),
  getEntriesByDate: (date: string, platform?: string) => 
    api.get<DayRecommendationResponse[]>(`/entries/${date}`, { params: { platform } }),
  regenerate: (planId: number, date: string, data: RegenerateRequest, platform?: string) =>
    api.post<RegenerateResponse>(`/plans/${planId}/entries/${date}/regenerate`, data, { params: { platform } }),
  regenerateById: (entryId: number, data: RegenerateRequest) =>
    api.post<RegenerateResponse>(`/entries/by-id/${entryId}/regenerate`, data),
  generateImage: (planId: number, date: string, data: ImageGenerateRequest, platform?: string) =>
    api.post<ImageGenerateResponse>(`/plans/${planId}/entries/${date}/image`, data, { params: { platform } }),
  generateImageById: (entryId: number, data: ImageGenerateRequest) =>
    api.post<ImageGenerateResponse>(`/entries/by-id/${entryId}/image`, data),
  regenerateImagePrompt: (entryId: number) =>
    api.post(`/entries/by-id/${entryId}/regenerate-image-prompt`),
  getJobs: (planId: number) => api.get<PlanJobsResponse>(`/plans/${planId}/jobs`),
};

export const knowledgeApi = {
  update: (data: BrandKnowledgeUpdateRequest) => 
    api.post<BrandKnowledgeUpdateResponse>('/knowledge/update', data),
  status: () => api.get<{ total_documents: number; products: any[] }>('/knowledge/status'),
};

export default api;