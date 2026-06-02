import { useEffect, useMemo, useState, type FormEvent } from "react";
import { api } from "./api";
import type { AlertRow, Rule, RulePayload } from "./types";

function isoMinusMinutes(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
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
  return {
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
  };
}

export default function App() {
  const [sim, setSim] = useState<any>(null);
  const [anStatus, setAnStatus] = useState<any>(null);
  const [live, setLive] = useState<Record<string, unknown> | null>(null);
  const [byType, setByType] = useState<Record<string, unknown> | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState("");
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);

  const [deviceCount, setDeviceCount] = useState(100);
  const [frequencySeconds, setFrequencySeconds] = useState(1);
  const [batchSize, setBatchSize] = useState(100);
  const [method, setMethod] = useState("Parallel");

  const [rule, setRule] = useState<RulePayload>(() => createEmptyRule());

  const from = useMemo(() => isoMinusMinutes(10), []);
  const to = useMemo(() => new Date().toISOString(), []);

  function resetRuleForm() {
    setEditingRuleId(null);
    setRule(createEmptyRule());
  }

  async function loadAll() {
    try {
      setError("");
      const [s, a, l, t, rep, al, rs] = await Promise.all([
        api.simulatorStatus(),
        api.analyticsStatus(),
        api.analyticsLiveSummary(),
        api.analyticsLiveByType(),
        api.analyticsReportWindow(from, to),
        api.alerts(20),
        api.rules()
      ]);
      setSim(s);
      setAnStatus(a);
      setLive(l);
      setByType(t);
      setReport(rep);
      setAlerts(al);
      setRules(rs);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
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
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void loadAll();
    const timer = setInterval(() => {
      void loadAll();
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <main className="layout">
      <header className="top">
        <h1>IoT Dashboard</h1>
        <button onClick={() => void loadAll()}>Refresh</button>
      </header>
      {error && <div className="error">{error}</div>}

      <section className="grid">
        <article className="panel">
          <h2>Simulator</h2>
          <p>Status: {sim?.running ? "Running" : "Stopped"}</p>
          <div className="row">
            <input type="number" value={deviceCount} onChange={(e) => setDeviceCount(Number(e.target.value))} />
            <input
              type="number"
              value={frequencySeconds}
              onChange={(e) => setFrequencySeconds(Number(e.target.value))}
            />
          </div>
          <div className="row">
            <button onClick={() => void api.simulatorConfig(deviceCount, frequencySeconds).then(loadAll)}>
              Apply Config
            </button>
            <button onClick={() => void api.simulatorStart().then(loadAll)}>Start</button>
            <button onClick={() => void api.simulatorStop().then(loadAll)}>Stop</button>
          </div>
        </article>

        <article className="panel">
          <h2>Analytics</h2>
          <p>Method: {anStatus?.method}</p>
          <div className="row">
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option>Parallel</option>
              <option>Sequential</option>
            </select>
            <input type="number" value={batchSize} onChange={(e) => setBatchSize(Number(e.target.value))} />
            <button onClick={() => void api.analyticsConfig(method, batchSize).then(loadAll)}>Apply</button>
          </div>
          <pre>{JSON.stringify(live, null, 2)}</pre>
          <pre>{JSON.stringify(byType, null, 2)}</pre>
          <pre>{JSON.stringify(report, null, 2)}</pre>
        </article>

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

        <article className="panel">
          <h2>Rules</h2>
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
                <input
                  id="rule-field"
                  value={rule.field}
                  onChange={(e) => setRule({ ...rule, field: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="rule-operator">Operator</label>
                <input
                  id="rule-operator"
                  value={rule.operator}
                  onChange={(e) => setRule({ ...rule, operator: e.target.value })}
                />
              </div>
            </div>
            <div className="row">
              <div className="field">
                <label htmlFor="rule-threshold">Threshold</label>
                <input
                  id="rule-threshold"
                  type="number"
                  value={rule.thresholdNumber ?? 0}
                  onChange={(e) => setRule({ ...rule, thresholdNumber: Number(e.target.value) })}
                />
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
                    {r.type} | {r.severity} | {r.field} {r.operator} {r.thresholdNumber ?? "-"}
                  </span>
                </div>
                <div className="row item-actions">
                  <button type="button" onClick={() => beginEdit(r)}>
                    Edit
                  </button>
                  <button type="button" onClick={() => void api.deleteRule(r.id).then(loadAll)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
