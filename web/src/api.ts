import type {
  PersonalizedResearchRequest,
  PreferredSourcesConfig,
  PreferredSourcesConfigOut,
  PromptConfig,
  PromptConfigOut,
  ResearchDetail,
  ResearchListResponse,
  ResearchRunRequest,
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
