export type SimulatorStatus = {
  running: boolean;
  deviceCount: number;
  frequencySeconds: number;
  batchSize: number;
};

export type AnalyticsStatus = {
  method: string;
  batchSize: number;
};

export type Rule = {
  id: string;
  name: string;
  type: "INSTANT" | "DURATION";
  severity: "WARNING" | "CRITICAL";
  field: string;
  operator: string;
  thresholdNumber?: number | null;
  thresholdBoolean?: boolean | null;
  thresholdText?: string | null;
  requiredPackets: number;
  cooldownSeconds: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
};

export type RulePayload = {
  name: string;
  type: "INSTANT" | "DURATION";
  severity: "WARNING" | "CRITICAL";
  field: string;
  operator: string;
  thresholdNumber?: number;
  thresholdBoolean?: boolean;
  thresholdText?: string;
  requiredPackets: number;
  cooldownSeconds: number;
  enabled: boolean;
};

export type AlertRow = {
  id: string;
  deviceId: number;
  ruleName: string;
  severity: string;
  currentValue: unknown;
  threshold: unknown;
  receivedAt: string;
};
