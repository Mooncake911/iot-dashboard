import logging
from typing import Any, Optional

import requests

from dashboard.mock import is_mock_mode, MockHTTPClient

logger = logging.getLogger(__name__)


class APIResponse:
    """Structured API response with status, body, and error information."""

    def __init__(self, status: Optional[int] = None, body: Any = None, error: Optional[str] = None, url: str = ""):
        self.status = status
        self.body = body
        self.error = error
        self.url = url

    def to_dict(self) -> dict:
        """Convert response to dictionary for display."""
        result = {}
        if self.status is not None:
            result["status"] = self.status
        if self.body is not None:
            result["body"] = self.body
        if self.error is not None:
            result["error"] = self.error
            result["url"] = self.url
        return result

    def is_success(self) -> bool:
        """Check if the request was successful."""
        return self.status is not None and 200 <= self.status < 300


def request(method: str, url: str, timeout: int = 10, **kwargs) -> dict:
    """
    Make an HTTP request with improved error handling and logging.
    In mock mode, delegates to MockHTTPClient.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests.request
        
    Returns:
        Dictionary with status, body, and optional error information
    """
    if is_mock_mode():
        logger.info(f"[MOCK] {method} {url}")
        return MockHTTPClient.request(method, url, timeout, **kwargs)

    try:
        logger.debug(f"{method} {url}")
        response = requests.request(method, url, timeout=timeout, **kwargs)

        # Parse response based on content type
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                body = response.json()
            except ValueError:
                body = response.text
        else:
            body = response.text

        api_response = APIResponse(status=response.status_code, body=body, url=url)

        if not api_response.is_success():
            logger.warning(f"Request failed: {method} {url} - Status {response.status_code}")

        return api_response.to_dict()

    except requests.exceptions.Timeout:
        error_msg = f"Request timeout after {timeout}s"
        logger.error(f"{error_msg}: {method} {url}")
        return APIResponse(error=error_msg, url=url).to_dict()

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(f"{error_msg}: {method} {url}")
        return APIResponse(error=error_msg, url=url).to_dict()

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(f"{error_msg}: {method} {url}")
        return APIResponse(error=error_msg, url=url).to_dict()

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{error_msg}: {method} {url}")
        return APIResponse(error=error_msg, url=url).to_dict()
