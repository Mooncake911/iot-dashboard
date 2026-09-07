import type {
  AlertRow,
  AnalyticsStatus,
  Rule,
  RulePayload,
  SimulatorStatus
} from "./types";

const GATEWAY =
  (import.meta as { env?: Record<string, string> }).env?.VITE_GATEWAY_URL ??
  "http://localhost:8085";
const BASE = GATEWAY ? `${GATEWAY}/api/v1` : "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  simulatorStatus: () => request<SimulatorStatus>("/simulator/status"),
  simulatorConfig: (deviceCount: number, frequencySeconds: number) =>
    request<string>(
      `/simulator/config?deviceCount=${deviceCount}&frequencySeconds=${frequencySeconds}`,
      { method: "POST" }
    ),
  simulatorStart: () => request<void>("/simulator/start", { method: "POST" }),
  simulatorStop: () => request<void>("/simulator/stop", { method: "POST" }),

  analyticsStatus: () => request<AnalyticsStatus>("/analytics/status"),
  analyticsConfig: (method: string, windowSeconds: number) =>
    request<string>(
      `/analytics/config?method=${encodeURIComponent(method)}&windowSeconds=${windowSeconds}`,
      { method: "POST" }
    ),
  analyticsLiveSummary: () => request<Record<string, unknown>>("/analytics/live/summary"),
  analyticsLiveByType: () => request<Record<string, unknown>>("/analytics/live/by-type"),
  analyticsLiveByManufacturer: () => request<Record<string, unknown>>("/analytics/live/by-manufacturer"),
  analyticsReportWindow: (from: string, to: string) =>
    request<Record<string, unknown>>(`/analytics/report/window?from=${from}&to=${to}`),

  alerts: (limit = 20) => request<AlertRow[]>(`/alerts?limit=${limit}`),
  rules: () => request<Rule[]>("/alerts/rules"),
  createRule: (payload: RulePayload) =>
    request<Rule>("/alerts/rules", { method: "POST", body: JSON.stringify(payload) }),
  updateRule: (id: string, payload: RulePayload) =>
    request<Rule>(`/alerts/rules/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteRule: (id: string) => request<void>(`/alerts/rules/${id}`, { method: "DELETE" })
};
