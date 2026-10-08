import type {
  CareerTwin,
  CareerSwitchAnalysis,
  CareerSwitchRequest,
  AIRiskAnalysis,
  AIRiskCatalog,
  MarketCatalogEntry,
  MarketCode,
  MarketIntelligence,
  MarketRefreshResult,
  StudentProfile,
  StudentProfileInput,
  AuthUser,
} from "./types";
import type {
  CareerSimulations,
  SimulationMarketCode,
  WhatIfComparison,
  WhatIfScenario,
} from "./types";

const API_ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");
const API_BASE_URL = API_ORIGIN ? `${API_ORIGIN}/api` : "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError("Can't reach CareerTwin right now. Check that the backend is running and try again.", 0);
  }

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/")) {
      window.dispatchEvent(new CustomEvent("careertwin:unauthorized"));
    }
    let message = `CareerTwin couldn't complete that request (${response.status}).`;
    try {
      const detail = (await response.json()) as { detail?: string };
      if (detail.detail) message = detail.detail;
    } catch {
      // Keep the status-based message when the server response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function signUp(input: { name: string; email: string; password: string }): Promise<AuthUser> {
  return request<AuthUser>("/auth/signup", { method: "POST", body: JSON.stringify(input) });
}

export function logIn(input: { email: string; password: string }): Promise<AuthUser> {
  return request<AuthUser>("/auth/login", { method: "POST", body: JSON.stringify(input) });
}

export function getCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>("/auth/me");
}

export function logOut(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" });
}

export function getProfile(profileId: number): Promise<StudentProfile> {
  return request<StudentProfile>(`/profiles/${profileId}`);
}

export function saveProfile(
  input: StudentProfileInput,
  profileId?: number,
): Promise<StudentProfile> {
  return request<StudentProfile>(profileId ? `/profiles/${profileId}` : "/profiles", {
    method: profileId ? "PUT" : "POST",
    body: JSON.stringify(input),
  });
}

export function generateCareerTwin(profileId: number, market: "IN" | "US" = "IN"): Promise<CareerTwin> {
  return request<CareerTwin>(`/profiles/${profileId}/careertwin?market=${market}`, { method: "POST" });
}

export function getMarkets(): Promise<{ markets: MarketCatalogEntry[] }> {
  return request<{ markets: MarketCatalogEntry[] }>("/markets");
}

export function getMarketIntelligence(market: MarketCode): Promise<MarketIntelligence> {
  return request<MarketIntelligence>(`/market-intelligence?market=${market}`);
}

export function getAiRiskCatalog(market: SimulationMarketCode): Promise<AIRiskCatalog> {
  return request<AIRiskCatalog>(`/ai-risk?market=${market}`);
}

export function analyzeAiRisk(
  careerId: string,
  profileId: number,
  market: SimulationMarketCode,
  scenario: WhatIfScenario,
): Promise<AIRiskAnalysis> {
  return request<AIRiskAnalysis>(`/ai-risk/${encodeURIComponent(careerId)}/analysis`, {
    method: "POST",
    body: JSON.stringify({ profile_id: profileId, market, what_if: scenario }),
  });
}

export function runDemoMarketUpdate(
  profileId: number,
  market: "IN" | "US",
  careerId = "product-analyst",
  action: "apply" | "reset" = "apply",
): Promise<MarketRefreshResult> {
  return request<MarketRefreshResult>(
    `/profiles/${profileId}/market-intelligence/${market}/demo-update?career_id=${encodeURIComponent(careerId)}&action=${action}`,
    { method: "POST" },
  );
}

export function getCareerSimulations(market: SimulationMarketCode): Promise<CareerSimulations> {
  return request<CareerSimulations>(`/simulations?market=${market}`);
}

export function runWhatIf(
  profileId: number,
  scenario: WhatIfScenario,
  market: SimulationMarketCode,
): Promise<WhatIfComparison> {
  return request<WhatIfComparison>(`/profiles/${profileId}/what-if?market=${market}`, {
    method: "POST",
    body: JSON.stringify(scenario),
  });
}

export function runCareerSwitch(requestBody: CareerSwitchRequest): Promise<CareerSwitchAnalysis> {
  return request<CareerSwitchAnalysis>("/career-switch", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}
