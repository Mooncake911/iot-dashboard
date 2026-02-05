from dashboard.services.base import BaseService
import logging

logger = logging.getLogger(__name__)

class SimulatorService(BaseService):
    def get_status(self) -> dict:
        """Fetch simulator status."""
        return self._get("/api/simulator/status")

    def toggle_simulator(self, run: bool) -> bool:
        """Start or stop the simulator."""
        action = "stop" if run else "start"
        return self._post(f"/api/simulator/{action}")

    def update_config(self, device_count: int, messages_per_second: int) -> bool:
        """Update simulator configuration."""
        # Clean parameter passing
        return self._post(
            "/api/simulator/config", 
            params={"deviceCount": device_count, "messagesPerSecond": messages_per_second}
        )
