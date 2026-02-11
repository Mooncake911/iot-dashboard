from typing import TypedDict, Literal, Dict

Severity = Literal["INFO", "WARNING", "CRITICAL"]

class Alert(TypedDict):
    _id: str
    ruleId: str
    severity: Severity
    deviceId: int
    message: str
    receivedAt: str
    value: float
    threshold: float

class BatteryMetrics(TypedDict):
    avg: float
    min: float
    max: float

class SignalMetrics(TypedDict):
    avg: float
    min: float
    max: float

class HeartbeatMetrics(TypedDict):
    avg: float
    min: float
    max: float

class AnalyticsMetrics(TypedDict):
    totalDevices: float
    onlineDevices: float
    coverageVolume: float
    battery: BatteryMetrics
    signal: SignalMetrics
    heartbeat: HeartbeatMetrics
    byType: Dict[str, float]
    byManufacturer: Dict[str, float]

class AnalyticsPoint(TypedDict):
    _id: str
    deviceId: int
    timestamp: str
    metrics: AnalyticsMetrics
