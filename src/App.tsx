import { useEffect, useState, type FormEvent } from "react";
import { api } from "./api";
import type { AlertRow, AnalyticsStatus, Rule, RulePayload, SimulatorStatus } from "./types";

const RULE_FIELDS = {
  BATTERY_LEVEL: {
    label: "Battery level",
    kind: "number",
    operators: ["LT", "LTE", "GT", "GTE", "EQ", "NEQ"]
  },
  SIGNAL_STRENGTH: {
    label: "Signal strength",
    kind: "number",
    operators: ["LT", "LTE", "GT", "GTE", "EQ", "NEQ"]
  },
  DEVICE_NAME: {
    label: "Device name",
    kind: "text",
    operators: ["EQ", "NEQ", "CONTAINS"]
  },
  MANUFACTURER: {
    label: "Manufacturer",
    kind: "text",
    operators: ["EQ", "NEQ", "CONTAINS"]
  },
  DEVICE_TYPE: {
    label: "Device type",
    kind: "text",
    operators: ["EQ", "NEQ", "CONTAINS"]
  },
  IS_ONLINE: {
    label: "Is online",
    kind: "boolean",
    operators: ["EQ", "NEQ"]
  }
} as const;

type RuleFieldKey = keyof typeof RULE_FIELDS;
type RuleFieldKind = (typeof RULE_FIELDS)[RuleFieldKey]["kind"];

function isoMinusMinutes(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

function isoToDateTimeLocal(value: string): string {
  const date = new Date(value);
  const pad = (n: number) => String(n).padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join("-") + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function dateTimeLocalToIso(value: string): string {
  return new Date(value).toISOString();
}

function createEmptyRule(): RulePayload {
  return {
    name: "low-battery",
    type: "DURATION",
    severity: "WARNING",
    field: "BATTERY_LEVEL",
    operator: "LT",
    thresholdNumber: 20,
    requiredPackets: 3,
    cooldownSeconds: 30,
    enabled: true
  };
}

function ruleToDraft(rule: Rule): RulePayload {
  return withFieldDefaults((rule.field as RuleFieldKey) ?? "BATTERY_LEVEL", {
    name: rule.name,
    type: rule.type,
    severity: rule.severity,
    field: rule.field,
    operator: rule.operator,
    thresholdNumber: rule.thresholdNumber ?? undefined,
    thresholdBoolean: rule.thresholdBoolean ?? undefined,
    thresholdText: rule.thresholdText ?? undefined,
    requiredPackets: rule.requiredPackets,
    cooldownSeconds: rule.cooldownSeconds,
    enabled: rule.enabled
  });
}

function getFieldConfig(field: string) {
  return RULE_FIELDS[field as RuleFieldKey] ?? RULE_FIELDS.BATTERY_LEVEL;
}

function withFieldDefaults(field: RuleFieldKey, current: RulePayload): RulePayload {
  const config = RULE_FIELDS[field];
  const operators = config.operators as readonly string[];
  const nextOperator = operators.includes(current.operator)
    ? current.operator
    : operators[0];

  if (config.kind === "number") {
    return {
      ...current,
      field,
      operator: nextOperator,
      thresholdNumber: current.thresholdNumber ?? 0,
      thresholdBoolean: undefined,
      thresholdText: undefined
    };
  }

  if (config.kind === "boolean") {
    return {
      ...current,
      field,
      operator: nextOperator,
      thresholdNumber: undefined,
      thresholdBoolean: current.thresholdBoolean ?? true,
      thresholdText: undefined
    };
  }

  return {
    ...current,
    field,
    operator: nextOperator,
    thresholdNumber: undefined,
    thresholdBoolean: undefined,
    thresholdText: current.thresholdText ?? ""
  };
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"monitoring" | "management">("monitoring");
  const [sim, setSim] = useState<SimulatorStatus | null>(null);
  const [anStatus, setAnStatus] = useState<AnalyticsStatus | null>(null);
  const [live, setLive] = useState<Record<string, unknown> | null>(null);
  const [byType, setByType] = useState<Record<string, unknown> | null>(null);
  const [byManufacturer, setByManufacturer] = useState<Record<string, unknown> | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState("");
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [reportFrom, setReportFrom] = useState(() => isoToDateTimeLocal(isoMinusMinutes(10)));
  const [reportTo, setReportTo] = useState(() => isoToDateTimeLocal(new Date().toISOString()));

  const [deviceCount, setDeviceCount] = useState(100);
  const [frequencySeconds, setFrequencySeconds] = useState(1);
  const [windowSeconds, setWindowSeconds] = useState(30);
  const [method, setMethod] = useState("Parallel");
  const [simulatorTogglePending, setSimulatorTogglePending] = useState(false);
  const [simulatorConfigPending, setSimulatorConfigPending] = useState(false);
  const [analyticsConfigPending, setAnalyticsConfigPending] = useState(false);
  const [reportPending, setReportPending] = useState(false);

  const [rule, setRule] = useState<RulePayload>(() => createEmptyRule());

  function resetRuleForm() {
    setEditingRuleId(null);
    setRule(createEmptyRule());
  }

  async function loadRealtime() {
    try {
      setError("");
      const [s, a, l, t, m, al, rs] = await Promise.all([
        api.simulatorStatus(),
        api.analyticsStatus(),
        api.analyticsLiveSummary(),
        api.analyticsLiveByType(),
        api.analyticsLiveByManufacturer(),
        api.alerts(20),
        api.rules()
      ]);
      setSim(s);
      setAnStatus(a);
      setWindowSeconds(Number(a?.windowSeconds ?? 30));
      setLive(l);
      setByType(t);
      setByManufacturer(m);
      setAlerts(al);
      setRules(rs);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function loadReport() {
    setReportPending(true);
    try {
      setError("");
      const rep = await api.analyticsReportWindow(
        dateTimeLocalToIso(reportFrom),
        dateTimeLocalToIso(reportTo)
      );
      setReport(rep);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setReportPending(false);
    }
  }

  async function refreshDashboard() {
    await Promise.all([loadRealtime(), loadReport()]);
  }

  function beginEdit(selectedRule: Rule) {
    setEditingRuleId(selectedRule.id);
    setRule(ruleToDraft(selectedRule));
  }

  async function submitRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setError("");
      if (editingRuleId) {
        await api.updateRule(editingRuleId, rule);
      } else {
        await api.createRule(rule);
      }
      resetRuleForm();
      await loadRealtime();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void refreshDashboard();
    const timer = setInterval(() => {
      void loadRealtime();
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const simulatorRunning = Boolean(sim?.running);
  const activeField = getFieldConfig(rule.field);
  const realtimeCards = [
    { label: "Unique devices", value: live?.totalUniqueDevices },
    { label: "Online count", value: live?.onlineCount },
    { label: "Offline", value: live?.offlineCount },
    { label: "Online rate", value: formatPercent(live?.onlineRate) },
    { label: "Avg battery", value: formatPercentFromWhole(live?.avgBatteryLevel) },
    { label: "Avg signal", value: formatPercentFromWhole(live?.avgSignalStrength) },
    { label: "Low battery", value: live?.lowBatteryCount },
    { label: "Weak signal", value: live?.weakSignalCount }
  ];

  const typeCounts = sortEntries(byType?.types);
  const ruleStats = {
    total: rules.length,
    enabled: rules.filter((r) => r.enabled).length,
    disabled: rules.filter((r) => !r.enabled).length,
    duration: rules.filter((r) => r.type === "DURATION").length,
    instant: rules.filter((r) => r.type === "INSTANT").length
  };

  function toggleSimulator() {
    setSimulatorTogglePending(true);
    if (simulatorRunning) {
      return api.simulatorStop()
        .then(loadRealtime)
        .finally(() => setSimulatorTogglePending(false));
    }
    return api.simulatorStart()
      .then(loadRealtime)
      .finally(() => setSimulatorTogglePending(false));
  }

  function applySimulatorConfig() {
    setSimulatorConfigPending(true);
    return api.simulatorConfig(deviceCount, frequencySeconds)
      .then(loadRealtime)
      .finally(() => setSimulatorConfigPending(false));
  }

  function applyAnalyticsConfig() {
    setAnalyticsConfigPending(true);
    return api.analyticsConfig(method, windowSeconds)
      .then(loadRealtime)
      .finally(() => setAnalyticsConfigPending(false));
  }

  function updateRuleField(field: RuleFieldKey) {
    setRule((current) => withFieldDefaults(field, current));
  }

  function updateRuleOperator(operator: string) {
    setRule((current) => ({ ...current, operator }));
  }

  function renderThresholdInput(kind: RuleFieldKind) {
    if (kind === "boolean") {
      return (
        <select
          id="rule-threshold"
          value={String(rule.thresholdBoolean ?? true)}
          onChange={(e) => setRule({ ...rule, thresholdBoolean: e.target.value === "true" })}
        >
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      );
    }

    if (kind === "text") {
      return (
        <input
          id="rule-threshold"
          value={rule.thresholdText ?? ""}
          onChange={(e) => setRule({ ...rule, thresholdText: e.target.value })}
        />
      );
    }

    return (
      <input
        id="rule-threshold"
        type="number"
        value={rule.thresholdNumber ?? 0}
        onChange={(e) => setRule({ ...rule, thresholdNumber: Number(e.target.value) })}
      />
    );
  }

  return (
    <main className="layout">
      <header className="top">
        <h1>IoT Dashboard</h1>
        <div className="header-actions">
          <button className="secondary" onClick={() => void refreshDashboard()}>
            Refresh
          </button>
        </div>
      </header>
      {error && <div className="error">{error}</div>}
      <div className="tabs" role="tablist" aria-label="Dashboard sections">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "monitoring"}
          className={activeTab === "monitoring" ? "tab active" : "tab"}
          onClick={() => setActiveTab("monitoring")}
        >
          Monitoring
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "management"}
          className={activeTab === "management" ? "tab active" : "tab"}
          onClick={() => setActiveTab("management")}
        >
          Alerts & Rules
        </button>
      </div>

      <section className={activeTab === "monitoring" ? "grid grid-single" : "grid"}>
        {activeTab === "monitoring" && (
          <>
        <article className="panel">
          <h2>Simulator</h2>
          <div className="status-line">
            <span className={simulatorRunning ? "badge success" : "badge muted"}>
              {simulatorRunning ? "Running" : "Stopped"}
            </span>
            <span className="meta">
              Devices {sim?.deviceCount ?? 0} | Frequency {sim?.frequencySeconds ?? 0}s | Batch {sim?.batchSize ?? 0}
            </span>
          </div>
          <div className="row">
            <input type="number" value={deviceCount} onChange={(e) => setDeviceCount(Number(e.target.value))} />
            <input
              type="number"
              value={frequencySeconds}
              onChange={(e) => setFrequencySeconds(Number(e.target.value))}
            />
          </div>
          <div className="row">
            <button
              className={simulatorConfigPending ? "muted-action" : undefined}
              disabled={simulatorConfigPending}
              onClick={() => void applySimulatorConfig()}
            >
              Apply Config
            </button>
            <button
              className={
                simulatorTogglePending
                  ? "muted-action"
                  : simulatorRunning
                    ? "danger"
                    : "success"
              }
              disabled={simulatorTogglePending}
              onClick={() => void toggleSimulator()}
            >
              {simulatorRunning ? "Stop" : "Start"}
            </button>
          </div>
        </article>

        <article className="panel">
          <h2>Analytics</h2>
          <p>
            Method: {anStatus?.method} | Window {renderValue(anStatus?.windowSeconds ?? windowSeconds)}s
          </p>
          <div className="analytics-config">
            <div className="row">
              <div className="field">
                <label htmlFor="analytics-method">Calculation method</label>
                <select id="analytics-method" value={method} onChange={(e) => setMethod(e.target.value)}>
                  <option>Parallel</option>
                  <option>Sequential</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="analytics-window">Analytics window duration (s)</label>
                <input
                  id="analytics-window"
                  type="number"
                  min={1}
                  value={windowSeconds}
                  onChange={(e) => setWindowSeconds(Number(e.target.value))}
                />
              </div>
              <button
                className={analyticsConfigPending ? "muted-action" : undefined}
                disabled={analyticsConfigPending}
                onClick={() => void applyAnalyticsConfig()}
              >
                Apply
              </button>
            </div>
            <p className="helper">
              Window duration controls how long incoming unique device states are accumulated before one historical snapshot is saved.
            </p>
          </div>
          <div className="analytics-block">
            <div className="section-head">
              <h3>Real-time</h3>
              <span className="meta">Current unique device snapshot</span>
            </div>
            <div className="metric-grid">
              {realtimeCards.map((card) => (
                <div key={card.label} className="metric-card">
                  <span>{card.label}</span>
                  <strong>{renderValue(card.value)}</strong>
                </div>
              ))}
            </div>
            <div className="subgrid">
              <div className="panel-lite">
                <h4>Type distribution</h4>
                <div className="bar-list">
                  {typeCounts.map(([type, count]) => (
                    <div key={type} className="bar-row">
                      <span>{type}</span>
                      <strong>{count as number}</strong>
                    </div>
                  ))}
                </div>
              </div>
              <div className="panel-lite">
                <h4>Manufacturer distribution</h4>
                <div className="bar-list">
                  {sortEntries(byManufacturer?.manufacturers).map(([manufacturer, count]) => (
                    <div key={manufacturer} className="bar-row">
                      <span>{manufacturer}</span>
                      <strong>{renderValue(count)}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="analytics-block">
            <div className="section-head">
              <h3>Window report</h3>
              <span className="meta">Aggregated history for a selected range</span>
            </div>
            <div className="row">
              <div className="field">
                <label htmlFor="report-from">From</label>
                <input
                  id="report-from"
                  type="datetime-local"
                  value={reportFrom}
                  onChange={(e) => setReportFrom(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="report-to">To</label>
                <input
                  id="report-to"
                  type="datetime-local"
                  value={reportTo}
                  onChange={(e) => setReportTo(e.target.value)}
                />
              </div>
              <button
                className={reportPending ? "muted-action" : undefined}
                disabled={reportPending}
                onClick={() => void loadReport()}
              >
                Apply range
              </button>
            </div>
            <div className="metric-grid report-grid">
              <Metric label="Records" value={report?.windows} />
              <Metric label="Online rate" value={formatPercent(report?.onlineRate)} />
              <Metric label="Avg battery" value={formatPercentFromWhole(report?.avgBatteryLevel)} />
              <Metric label="Avg signal" value={formatPercentFromWhole(report?.avgSignalStrength)} />
            </div>
            <div className="panel-lite">
              <h4>Range snapshot</h4>
              <dl className="kv-list">
                <div>
                  <dt>From</dt>
                  <dd>{renderValue(report?.from)}</dd>
                </div>
                <div>
                  <dt>To</dt>
                  <dd>{renderValue(report?.to)}</dd>
                </div>
              </dl>
            </div>
          </div>
        </article>
          </>
        )}

        {activeTab === "management" && (
        <article className="panel">
          <div className="section-head">
            <h2>Rules</h2>
            <span className="meta">
              Total {ruleStats.total} | Enabled {ruleStats.enabled} | Disabled {ruleStats.disabled}
            </span>
          </div>
          <div className="rule-summary">
            <span className="badge muted">Instant {ruleStats.instant}</span>
            <span className="badge muted">Duration {ruleStats.duration}</span>
          </div>
          <form className="col" onSubmit={(e) => void submitRule(e)}>
            <div className="field">
              <label htmlFor="rule-name">Name</label>
              <input
                id="rule-name"
                value={rule.name}
                onChange={(e) => setRule({ ...rule, name: e.target.value })}
              />
            </div>
            <div className="row">
              <div className="field">
                <label htmlFor="rule-type">Type</label>
                <select
                  id="rule-type"
                  value={rule.type}
                  onChange={(e) => setRule({ ...rule, type: e.target.value as any })}
                >
                  <option>DURATION</option>
                  <option>INSTANT</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="rule-severity">Severity</label>
                <select
                  id="rule-severity"
                  value={rule.severity}
                  onChange={(e) => setRule({ ...rule, severity: e.target.value as any })}
                >
                  <option>WARNING</option>
                  <option>CRITICAL</option>
                </select>
              </div>
            </div>
            <div className="row">
              <div className="field">
                <label htmlFor="rule-field">Field</label>
                <select
                  id="rule-field"
                  value={rule.field}
                  onChange={(e) => updateRuleField(e.target.value as RuleFieldKey)}
                >
                  {Object.entries(RULE_FIELDS).map(([value, config]) => (
                    <option key={value} value={value}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="rule-operator">Operator</label>
                <select
                  id="rule-operator"
                  value={rule.operator}
                  onChange={(e) => updateRuleOperator(e.target.value)}
                >
                  {activeField.operators.map((operator) => (
                    <option key={operator} value={operator}>
                      {operator}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="row">
              <div className="field">
                <label htmlFor="rule-threshold">Threshold</label>
                {renderThresholdInput(activeField.kind)}
              </div>
              <div className="field">
                <label htmlFor="rule-required-packets">Required Packets</label>
                <input
                  id="rule-required-packets"
                  type="number"
                  value={rule.requiredPackets}
                  onChange={(e) => setRule({ ...rule, requiredPackets: Number(e.target.value) })}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-cooldown">Cooldown</label>
                <input
                  id="rule-cooldown"
                  type="number"
                  value={rule.cooldownSeconds}
                  onChange={(e) => setRule({ ...rule, cooldownSeconds: Number(e.target.value) })}
                />
              </div>
            </div>
            <div className="row">
              <label className="toggle" htmlFor="rule-enabled">
                <input
                  id="rule-enabled"
                  type="checkbox"
                  checked={rule.enabled}
                  onChange={(e) => setRule({ ...rule, enabled: e.target.checked })}
                />
                Enabled
              </label>
            </div>
            <div className="row">
              <button type="submit">{editingRuleId ? "Save Changes" : "Create Rule"}</button>
              {editingRuleId && (
                <button type="button" onClick={resetRuleForm}>
                  Cancel
                </button>
              )}
            </div>
          </form>
          <div className="list">
            {rules.map((r) => (
              <div key={r.id} className="item">
                <div className="item-main">
                  <b>{r.name}</b>
                  <span>
                    {r.type} | {r.severity} | {r.field} {r.operator} {formatRuleThreshold(r)}
                  </span>
                </div>
                <div className="row item-actions">
                  <button type="button" onClick={() => beginEdit(r)}>
                    Edit
                  </button>
                  <button type="button" onClick={() => void api.deleteRule(r.id).then(loadRealtime)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>
        )}

        {activeTab === "management" && (
        <article className="panel">
          <h2>Alerts</h2>
          <div className="list">
            {alerts.map((a) => (
              <div key={a.id} className="item">
                <b>{a.severity}</b> device {a.deviceId} rule {a.ruleName}
              </div>
            ))}
          </div>
        </article>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{renderValue(value)}</strong>
    </div>
  );
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value);
}

function formatNumber(value: unknown): string {
  if (typeof value !== "number") {
    return renderValue(value);
  }
  return value.toFixed(2);
}

function formatPercent(value: unknown): string {
  if (typeof value !== "number") {
    return renderValue(value);
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatPercentFromWhole(value: unknown): string {
  if (typeof value !== "number") {
    return renderValue(value);
  }
  return `${value.toFixed(1)}%`;
}

function sortEntries(value: unknown): Array<[string, unknown]> {
  if (!value || typeof value !== "object") {
    return [];
  }
  return Object.entries(value as Record<string, unknown>).sort((a, b) => {
    const right = typeof b[1] === "number" ? b[1] : 0;
    const left = typeof a[1] === "number" ? a[1] : 0;
    return right - left;
  });
}

function formatRuleThreshold(rule: Rule): string {
  if (rule.thresholdNumber !== null && rule.thresholdNumber !== undefined) {
    return String(rule.thresholdNumber);
  }
  if (rule.thresholdBoolean !== null && rule.thresholdBoolean !== undefined) {
    return String(rule.thresholdBoolean);
  }
  if (rule.thresholdText) {
    return rule.thresholdText;
  }
  return "-";
}
