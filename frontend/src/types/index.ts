export type Platform = 'instagram' | 'linkedin';

export type ContentType = 
  | 'single_image' | 'carousel' | 'reel' | 'story' | 'story_sequence'
  | 'product_showcase' | 'educational' | 'problem_solution' | 'comparison'
  | 'community' | 'ugc_style' | 'promotional'
  | 'text_post' | 'image_post' | 'document_carousel' | 'brand_story'
  | 'industry_insight' | 'case_study';

export type PlanStatus = 'draft' | 'generating' | 'ready' | 'partial' | 'failed';

export type EntryStatus = 
  | 'planned' | 'queued' | 'generating' | 'ready' 
  | 'failed' | 'retrying' | 'skipped' | 'regenerating';

export type ImageStatus = 
  | 'not_requested' | 'queued' | 'generating' | 'ready' | 'failed';

export type ReviewStatus = 'pending' | 'approved' | 'needs_revision' | 'failed';

export interface CreatePlanRequest {
  start_date: string;
  end_date: string;
  platforms: Platform[];
  objective?: string;
  additional_instructions?: string;
}

export interface CreatePlanResponse {
  plan_id: number;
  status: PlanStatus;
}

export interface PlanResponse {
  plan_id: number;
  project_id: number;
  start_date: string;
  end_date: string;
  objective?: string;
  status: PlanStatus;
  strategy_summary?: string;
  created_at: string;
  updated_at: string;
}

export interface CalendarEntryBase {
  date: string;
  platform: Platform;
  content_type?: ContentType;
  status: EntryStatus;
  title?: string;
  objective?: string;
  content_pillar?: string;
  product?: string;
  audience?: string;
  hook?: string;
  concept?: string;
  caption_direction?: string;
  cta?: string;
  visual_direction?: string;
  image_prompt?: string;
  reason?: string;
  sequence_position?: number;
  campaign_thread?: string;
  follows_entry?: string;
  supports_entry?: string;
  review_status: ReviewStatus;
  review_score?: number;
  review_issues?: string[];
  review_corrections?: string[];
  review_attempts: number;
  error?: string;
  image_status: ImageStatus;
  image_url?: string;
  image_prompt_used?: string;
  image_prompts?: string[];
  image_urls?: string[];
  image_prompts_used?: string[];
}

export interface CalendarEntryResponse extends CalendarEntryBase {
  id: number;
  plan_id: number;
  created_at: string;
  updated_at: string;
}

export interface CalendarResponse {
  plan_id: number;
  start_date: string;
  end_date: string;
  strategy_summary?: string;
  recommended_frequency: Record<string, string>;
  entries: CalendarEntryResponse[];
  total_days: number;
  planned_posts: number;
  empty_days: number;
}

export interface DayRecommendationResponse {
  id?: number;
  plan_id?: number;
  date: string;
  platform: Platform;
  content_type?: ContentType;
  title?: string;
  objective?: string;
  audience?: string;
  product?: string;
  content_pillar?: string;
  reason?: string;
  hook?: string;
  concept?: string;
  caption_direction?: string;
  cta?: string;
  visual_direction?: string;
  image_prompt?: string;
  review_status: ReviewStatus;
  review_score?: number;
  review_issues?: string[];
  review_corrections?: string[];
  image_status: ImageStatus;
  image_url?: string;
  image_prompt_used?: string;
  image_prompts?: string[];
  image_urls?: string[];
  image_prompts_used?: string[];
  status: EntryStatus;
  error?: string;
  is_empty: boolean;
  empty_reason?: string;
}

export interface RegenerateRequest {
  feedback?: string;
}

export interface RegenerateResponse {
  date: string;
  status: EntryStatus;
}

export interface ImageGenerateRequest {
  prompt?: string;
  aspect_ratio?: string;
  model?: string;
  quality?: string;
  n?: number;
}

export interface ImageGenerateResponse {
  image_status: ImageStatus;
  image_url?: string;
  image_prompt_used?: string;
  image_urls?: string[];
  image_prompts_used?: string[];
}

export interface BrandKnowledgeUpdateRequest {
  force_reingest?: boolean;
}

export interface BrandKnowledgeUpdateResponse {
  success: boolean;
  message: string;
  version?: number;
}

export interface ErrorResponse {
  status: string;
  component: string;
  error_code: string;
  message: string;
  recoverable: boolean;
  retry_after?: number;
}

export interface HealthResponse {
  status: string;
  database: string;
  chromadb: string;
  llm_configured: boolean;
  image_provider_configured: boolean;
}

export interface JobStatusResponse {
  id: number;
  job_type: string;
  status: string;
  calendar_entry_id?: number;
  attempts: number;
  error?: string;
  created_at: string;
}

export interface PlanJobsResponse {
  jobs: JobStatusResponse[];
}