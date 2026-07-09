export type TrendCategory = "nails";

export interface LLMUsageStats {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface PromptConfig {
  version: number;
  neutral_system_prompt: string;
  personalized_system_prompt: string;
  web_grounded_rules: string;
  neutral_user_template: string;
  personalized_user_template: string;
}

export interface PromptConfigOut {
  config: PromptConfig;
  is_default: boolean;
}

export interface PreferredSource {
  name: string;
  domain: string;
  weight: number;
  categories: TrendCategory[];
  enabled: boolean;
}

export interface PreferredSourcesConfig {
  version: number;
  sources: PreferredSource[];
}

export interface PreferredSourcesConfigOut {
  config: PreferredSourcesConfig;
  is_default: boolean;
}

export interface TrendSignal {
  name: string;
  description: string;
  popularity: string;
  colors: string[];
  techniques: string[];
  tags: string[];
  confidence: number;
  source_hint: string;
  image_url: string | null;
  image_source_url: string | null;
  image_alt: string | null;
}

export interface WebCitation {
  title: string;
  url: string;
  snippet: string;
  preferred: boolean;
  source_name: string | null;
  query: string;
}

export interface WebResearchBundle {
  enabled: boolean;
  search_provider: string;
  queries: string[];
  citations: WebCitation[];
}

export interface TrendReport {
  category: TrendCategory;
  mode: string;
  research_time: string;
  summary: string;
  trends: TrendSignal[];
  generated_at: string;
  llm_provider: string;
  llm_model: string;
  llm_usage: LLMUsageStats | null;
  web_research: WebResearchBundle | null;
}

export interface UserPreferences {
  display_name: string;
  favorite_colors: string[];
  avoided_colors: string[];
  preferred_shapes: string[];
  preferred_lengths: string[];
  preferred_finishes: string[];
  style_keywords: string[];
  occasion: string | null;
  budget: string | null;
  notes: string | null;
}

export interface BriefCaption {
  locale: string;
  caption: string;
  cta: string | null;
}

export interface ProductServiceTieIn {
  service_suggestion: string;
  product_suggestion: string;
  rationale: string;
}

export interface ContentIdea {
  id: string;
  angles: string[];
  captions: BriefCaption[];
  hashtags: string[];
  posting_tip: string | null;
  product_mapping: ProductServiceTieIn | null;
  generated_at: string;
}

export interface BriefItem {
  id: string;
  rank: number;
  score: number;
  evidence_summary: string;
  why_now: string;
  caveats: string | null;
  trend: TrendSignal;
  content_idea: ContentIdea | null;
}

export interface TrendBrief {
  id: string;
  report_id: string;
  title: string;
  summary: string;
  region: string;
  research_time: string;
  generated_at: string;
  llm_provider: string;
  llm_model: string;
  llm_usage: LLMUsageStats | null;
  items: BriefItem[];
}

export interface ResearchListItem {
  id: string;
  category: TrendCategory;
  mode: "neutral" | "personalized";
  summary: string;
  region: string;
  research_time: string;
  generated_at: string;
  llm_provider: string;
  llm_model: string;
  llm_usage: LLMUsageStats | null;
  web_search_enabled: boolean;
  trend_count: number;
  citation_count: number;
  image_count: number;
  cover_image_url: string | null;
  created_at: string;
}

export interface ResearchDetail {
  id: string;
  region: string;
  research_time: string;
  web_search_enabled: boolean;
  preferences: UserPreferences | null;
  report: TrendReport;
}

export interface ResearchListResponse {
  items: ResearchListItem[];
  total: number;
}

export interface BriefGenerateRequest {
  report_id: string;
  trend_name?: string | null;
  provider?: string | null;
  max_trends?: number;
}

export interface ContentIdeaGenerateRequest {
  brief_item_id: string;
  provider?: string | null;
}

export interface ContentIdeaOut extends ContentIdea {
  brief_item_id: string;
}

export interface ResearchRunRequest {
  category?: TrendCategory;
  region?: string;
  research_time?: string | null;
  provider?: string | null;
  web_search?: boolean;
  search_provider?: string | null;
}

export interface PersonalizedResearchRequest extends ResearchRunRequest {
  preferences: UserPreferences;
}
