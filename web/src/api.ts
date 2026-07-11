import type {
  BriefGenerateRequest,
  ContentIdeaGenerateRequest,
  ContentIdeaOut,
  MediaJob,
  PersonalizedResearchRequest,
  PreferredSourcesConfig,
  PreferredSourcesConfigOut,
  PromptConfig,
  PromptConfigOut,
  ResearchDetail,
  ResearchListResponse,
  ResearchRunRequest,
  TrendBrief,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getMediaJob(jobId: string) {
  return request<MediaJob>(`/media-jobs/${jobId}`);
}

export function listResearch(limit = 50, offset = 0) {
  return request<ResearchListResponse>(`/research?limit=${limit}&offset=${offset}`);
}

export function getResearch(id: string) {
  return request<ResearchDetail>(`/research/${id}`);
}

export function runNeutralResearch(body: ResearchRunRequest) {
  return request<ResearchDetail>("/research/neutral", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function runPersonalizedResearch(body: PersonalizedResearchRequest) {
  return request<ResearchDetail>("/research/personalized", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function initBrief(body: { report_id: string; trend_name: string }) {
  return request<TrendBrief>("/briefs/init", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function generateBrief(body: BriefGenerateRequest) {
  return request<TrendBrief>("/briefs/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getBrief(id: string) {
  return request<TrendBrief>(`/briefs/${id}`);
}

export function getLatestBrief(reportId: string) {
  return request<TrendBrief>(`/briefs/latest?report_id=${encodeURIComponent(reportId)}`);
}

export function generateContentIdea(body: ContentIdeaGenerateRequest) {
  return request<ContentIdeaOut>("/ideas/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type MediaPromptTarget = {
  content_idea_id: string;
  kind: "image" | "video";
  sequence: number;
};

export function adjustMediaPrompt(
  body: MediaPromptTarget & {
    prompt: string;
    hook?: string | null;
    caption?: string;
    hashtags?: string[];
  },
) {
  return request<ContentIdeaOut>("/media-prompts", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function acceptMediaPrompt(body: MediaPromptTarget) {
  return request<ContentIdeaOut>("/media-prompts/accept", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type RegenerateField = "prompt" | "hook" | "caption" | "hashtags";

export function regenerateMediaPrompt(body: MediaPromptTarget & { field?: RegenerateField }) {
  return request<ContentIdeaOut>("/media-prompts/regenerate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function cancelMediaPrompt(body: MediaPromptTarget) {
  return request<ContentIdeaOut>("/media-prompts/cancel", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function reopenMediaPrompt(body: MediaPromptTarget) {
  return request<ContentIdeaOut>("/media-prompts/reopen", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getPrompts() {
  return request<PromptConfigOut>("/prompts");
}

export function updatePrompts(config: PromptConfig) {
  return request<PromptConfigOut>("/prompts", {
    method: "PUT",
    body: JSON.stringify(config),
  });
}

export function resetPrompts() {
  return request<PromptConfigOut>("/prompts/reset", {
    method: "POST",
  });
}

export function getSources() {
  return request<PreferredSourcesConfigOut>("/sources");
}

export function updateSources(config: PreferredSourcesConfig) {
  return request<PreferredSourcesConfigOut>("/sources", {
    method: "PUT",
    body: JSON.stringify(config),
  });
}

export function resetSources() {
  return request<PreferredSourcesConfigOut>("/sources/reset", {
    method: "POST",
  });
}
