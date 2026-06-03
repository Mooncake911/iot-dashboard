import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { api } from "./api";
import type { Rule } from "./types";

vi.mock("./api", () => ({
  api: {
    simulatorStatus: vi.fn(),
    simulatorConfig: vi.fn(),
    simulatorStart: vi.fn(),
    simulatorStop: vi.fn(),
    analyticsStatus: vi.fn(),
    analyticsConfig: vi.fn(),
    analyticsLiveSummary: vi.fn(),
    analyticsLiveByType: vi.fn(),
    analyticsLiveByManufacturer: vi.fn(),
    analyticsReportWindow: vi.fn(),
    alerts: vi.fn(),
    rules: vi.fn(),
    createRule: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn()
  }
}));

const mockedApi = api as unknown as {
  simulatorStatus: ReturnType<typeof vi.fn>;
  simulatorConfig: ReturnType<typeof vi.fn>;
  simulatorStart: ReturnType<typeof vi.fn>;
  simulatorStop: ReturnType<typeof vi.fn>;
  analyticsStatus: ReturnType<typeof vi.fn>;
  analyticsConfig: ReturnType<typeof vi.fn>;
  analyticsLiveSummary: ReturnType<typeof vi.fn>;
  analyticsLiveByType: ReturnType<typeof vi.fn>;
  analyticsLiveByManufacturer: ReturnType<typeof vi.fn>;
  analyticsReportWindow: ReturnType<typeof vi.fn>;
  alerts: ReturnType<typeof vi.fn>;
  rules: ReturnType<typeof vi.fn>;
  createRule: ReturnType<typeof vi.fn>;
  updateRule: ReturnType<typeof vi.fn>;
  deleteRule: ReturnType<typeof vi.fn>;
};

function makeRule(overrides: Partial<Rule> = {}): Rule {
  return {
    id: "rule-1",
    name: "low-battery",
    type: "DURATION",
    severity: "WARNING",
    field: "BATTERY_LEVEL",
    operator: "LT",
    thresholdNumber: 20,
    thresholdBoolean: null,
    thresholdText: null,
    requiredPackets: 3,
    cooldownSeconds: 30,
    enabled: true,
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
    ...overrides
  };
}

describe("Dashboard rules workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedApi.simulatorStatus.mockResolvedValue({
      running: false,
      deviceCount: 100,
      frequencySeconds: 1,
      batchSize: 100
    });
    mockedApi.analyticsStatus.mockResolvedValue({
      method: "Parallel",
      windowSeconds: 30
    });
    mockedApi.analyticsLiveSummary.mockResolvedValue({});
    mockedApi.analyticsLiveByType.mockResolvedValue({});
    mockedApi.analyticsLiveByManufacturer.mockResolvedValue({});
    mockedApi.analyticsReportWindow.mockResolvedValue({});
    mockedApi.alerts.mockResolvedValue([]);
    mockedApi.simulatorConfig.mockResolvedValue("ok");
    mockedApi.simulatorStart.mockResolvedValue(undefined);
    mockedApi.simulatorStop.mockResolvedValue(undefined);
    mockedApi.analyticsConfig.mockResolvedValue("ok");
    mockedApi.createRule.mockResolvedValue(makeRule());
    mockedApi.updateRule.mockResolvedValue(makeRule({ id: "rule-1", name: "updated" }));
    mockedApi.deleteRule.mockResolvedValue(undefined);
  });

  it("creates a new rule from the form", async () => {
    mockedApi.rules.mockResolvedValue([]);

    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Alerts & Rules" }));
    await screen.findByRole("heading", { name: "Rules" });
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "temperature-high" } });
    fireEvent.change(screen.getByLabelText("Field"), { target: { value: "SIGNAL_STRENGTH" } });
    fireEvent.change(screen.getByLabelText("Operator"), { target: { value: "GT" } });
    fireEvent.click(screen.getByRole("button", { name: "Create Rule" }));

    await waitFor(() => {
      expect(mockedApi.createRule).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "temperature-high",
          field: "SIGNAL_STRENGTH",
          operator: "GT"
        })
      );
    });
  });

  it("switches the form into edit mode and sends PUT on save", async () => {
    mockedApi.rules.mockResolvedValue([
      makeRule({
        id: "rule-9",
        name: "battery-low",
        field: "BATTERY_LEVEL",
        operator: "LT",
        thresholdNumber: 15
      })
    ]);

    render(<App />);

    fireEvent.click(screen.getByRole("tab", { name: "Alerts & Rules" }));
    await screen.findByText("battery-low");
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("button", { name: "Save Changes" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "battery-critical" } });
    fireEvent.change(screen.getByLabelText("Threshold"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(mockedApi.updateRule).toHaveBeenCalledWith(
        "rule-9",
        expect.objectContaining({
          name: "battery-critical",
          thresholdNumber: 10
        })
      );
    });
  });
});
