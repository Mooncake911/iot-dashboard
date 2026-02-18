# IoT Dashboard

**Real-time monitoring and control dashboard for IoT services**

A Streamlit-based web dashboard for monitoring and controlling the IoT microservices ecosystem, including data simulation, analytics, and alert monitoring.

---

## Features
- 🔄 **Simulator Control**: Single-toggle start/stop control with real-time status updates
- 📈 **Analytics Management**: Configure analytics processing methods and batch sizes with formatted status
- 🚨 **Alert Monitoring**: Real-time monitoring with color-coded severity levels (Red/Yellow/Green)
- 📊 **Metrics Dashboard**: Visual metrics for alerts, severities, and affected devices
- 🔌 **REST API Integration**: Full integration with all IoT service APIs
- 🧪 **Mock Mode**: Built-in simulation mode for local development without backend services
- 🗄️ **MongoDB Integration**: Direct connection to MongoDB for alert retrieval
- ⚙️ **Flexible Configuration**: YAML-based configuration with environment variable support

---

## Configuration

The dashboard uses YAML configuration (`application.yml`) with environment variable placeholder support.

### Configuration File Structure

```yaml
dashboard:
  mock-mode: ${MOCK_MODE:false}  # Enable/disable mock mode
  services:
    simulator:
      url: ${SIMULATOR_API_URL:http://localhost:8080}
    analytics:
      url: ${ANALYTICS_API_URL:http://localhost:8081}
    controller:
      url: ${CONTROLLER_API_URL:http://localhost:8082}
  
  mongodb:
    uri: ${MONGO_URI:mongodb://admin:admin@localhost:27017/iot_db?authSource=admin}
    database: ${MONGO_DB:iot_db}
    collections:
      alerts: ${MONGO_ALERTS_COLLECTION:alerts}
  
  ui:
    refresh-seconds-default: ${REFRESH_SECONDS_DEFAULT:2}
    alerts-limit-default: ${ALERTS_LIMIT_DEFAULT:50}
```

### Environment Variables

| Variable                  | Description                   | Default                 |
|---------------------------|-------------------------------|-------------------------|
| `MOCK_MODE`               | Enable mock mode (true/false) | `false`                 |
| `SIMULATOR_API_URL`       | Simulator service base URL    | `http://localhost:8080` |
| `ANALYTICS_API_URL`       | Analytics service base URL    | `http://localhost:8081` |
| `CONTROLLER_API_URL`      | Controller service base URL   | `http://localhost:8082` |
| `MONGO_URI`               | MongoDB connection URI        | `mongodb://...`         |
| `MONGO_DB`                | MongoDB database name         | `iot_db`                |
| `REFRESH_SECONDS_DEFAULT` | Default auto-refresh interval | `2`                     |

---

## Development Setup

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**:
   ```powershell
   cd d:\Projects\IDEA_Projects\IoT-service\iot-dashboard
   ```

2. **Install dependencies**:
   ```powershell
   uv sync
   # or
   pip install -e ".[dev]"
   ```

### Running Locally

1. **Run the dashboard**:
   ```powershell
   uv run streamlit run app.py
   ```

2. **Access the dashboard**:
   Open [http://localhost:8501](http://localhost:8501)

### Running in Mock Mode

Mock Mode allows you to run the dashboard entirely locally without any running backend services or MongoDB. It uses internal logic to simulate API responses and generate fake alerts.

```powershell
# Enable mock mode via environment variable
$env:MOCK_MODE="true"
uv run streamlit run app.py
```

**Mock Mode Features**:
- 🔌 **Simulated APIs**: Simulator and Analytics endpoints are mocked within the app
- 🚨 **Fake Data Generator**: Random alerts are generated for visualization
- ⚙️ **Auto-Configuration**: Uses internal defaults if config file is missing
- ⚠️ **Visual Component**: "⚠️ MOCK MODE ENABLED" warning in sidebar

---

## Usage

### Simulator Control
1. Go to **API Control** tab -> **Simulator** section.
2. Set `Device Count` and `Messages Per Second`.
3. Click **Set Configuration** to apply settings.
4. Use the **Start/Stop Simulator** toggle button to control execution.
5. Status metrics (State, Device Count, Rate) update automatically.

### Analytics Configuration
1. Go to **Analytics** section.
2. Select `Processing Method` and `Batch Size`.
3. Click **Set Configuration**.
4. Status metrics (Method, Batch Size) update automatically.

### Alert Monitoring
1. Go to **Alerts Monitor** tab.
2. Configure auto-refresh interval and alert limit.
3. View the **Alerts Table** with color-coded severity:
   - 🔴 **CRITICAL**: Red background
   - 🟡 **WARNING**: Yellow background
   - 🟢 **INFO**: Green background
4. Monitor metrics for total alerts, severities, and affected devices.

---

## Project Structure

```
iot-dashboard/
├── app.py                      # Main Streamlit application
├── application.yml             # Configuration file
├── pyproject.toml              # Dependencies (including pandas)
├── dashboard/
│   ├── config.py               # Config loading logic
│   ├── http_client.py          # HTTP client
│   ├── mock.py                 # Mock service implementations
│   ├── mock_data.py            # Shared mock data generators
│   ├── mongo_alerts.py         # MongoDB client
│   └── ui/
│       ├── api_tab.py          # API control interface
│       └── alerts_tab.py       # Alerts interface with styling
└── tests/
    ├── conftest.py             # Fixtures
    ├── test_config.py          # Config tests
    ├── test_mock.py            # Mock logic tests
    └── ...
```

---

## Troubleshooting

### Dashboard won't start

1. **Check configuration file exists**:
   ```powershell
   ls application.yml
   ```

2. **Verify dependencies are installed**:
   ```powershell
   uv sync
   ```

3. **Check Python version**:
   ```powershell
   python --version  # Should be 3.12+
   ```

### Can't connect to services

1. **Verify service URLs** in the sidebar configuration
2. **Check services are running**:
   ```powershell
   docker ps
   ```
3. **Test connectivity**:
   ```powershell
   curl http://localhost:8080/api/simulator/status
   ```

### MongoDB connection errors

1. **Verify MongoDB is running**:
   ```powershell
   docker logs mongodb
   ```

2. **Check connection string** in sidebar
3. **Verify credentials** match `.env` file

### Tests failing

1. **Install dev dependencies**:
   ```powershell
   uv sync --group dev
   ```

2. **Run tests with verbose output**:
   ```powershell
   uv run pytest tests/ -v -s
   ```

---

## License

Part of the IoT Service project.
