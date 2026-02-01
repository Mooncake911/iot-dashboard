"""Tests for HTTP client module."""

import responses

from dashboard.http_client import request, APIResponse


class TestAPIResponse:
    """Test APIResponse class."""

    def test_to_dict_success(self):
        """Test converting successful response to dict."""
        response = APIResponse(status=200, body={"message": "OK"}, url="http://test.com")
        result = response.to_dict()
        assert result["status"] == 200
        assert result["body"] == {"message": "OK"}
        assert "error" not in result

    def test_to_dict_error(self):
        """Test converting error response to dict."""
        response = APIResponse(error="Connection failed", url="http://test.com")
        result = response.to_dict()
        assert result["error"] == "Connection failed"
        assert result["url"] == "http://test.com"
        assert "status" not in result

    def test_is_success(self):
        """Test success status checking."""
        assert APIResponse(status=200).is_success()
        assert APIResponse(status=201).is_success()
        assert not APIResponse(status=404).is_success()
        assert not APIResponse(status=500).is_success()
        assert not APIResponse(error="Error").is_success()


class TestHTTPRequest:
    """Test HTTP request function."""

    @responses.activate
    def test_successful_json_request(self):
        """Test successful request with JSON response."""
        responses.add(
            responses.GET,
            "http://test.com/api/status",
            json={"status": "running"},
            status=200
        )

        result = request("GET", "http://test.com/api/status")
        assert result["status"] == 200
        assert result["body"] == {"status": "running"}
        assert "error" not in result

    @responses.activate
    def test_successful_text_request(self):
        """Test successful request with text response."""
        responses.add(
            responses.GET,
            "http://test.com/api/text",
            body="Plain text response",
            status=200,
            content_type="text/plain"
        )

        result = request("GET", "http://test.com/api/text")
        assert result["status"] == 200
        assert result["body"] == "Plain text response"

    @responses.activate
    def test_post_request_with_json(self):
        """Test POST request with JSON payload."""
        responses.add(
            responses.POST,
            "http://test.com/api/create",
            json={"id": 123, "created": True},
            status=201
        )

        result = request("POST", "http://test.com/api/create", json={"name": "test"})
        assert result["status"] == 201
        assert result["body"]["created"] is True

    @responses.activate
    def test_http_error_response(self):
        """Test handling of HTTP error responses."""
        responses.add(
            responses.GET,
            "http://test.com/api/notfound",
            json={"error": "Not found"},
            status=404
        )

        result = request("GET", "http://test.com/api/notfound")
        assert result["status"] == 404
        assert result["body"]["error"] == "Not found"

    def test_timeout_error(self):
        """Test handling of timeout errors."""
        # Use a non-routable IP to force timeout
        result = request("GET", "http://192.0.2.1:8080/api", timeout=1)
        assert "error" in result
        assert "timeout" in result["error"].lower() or "connection" in result["error"].lower()
        assert result["url"] == "http://192.0.2.1:8080/api"

    @responses.activate
    def test_invalid_json_response(self):
        """Test handling of invalid JSON in response."""
        responses.add(
            responses.GET,
            "http://test.com/api/invalid",
            body="Invalid JSON {",
            status=200,
            content_type="application/json"
        )

        result = request("GET", "http://test.com/api/invalid")
        assert result["status"] == 200
        # Should fallback to text when JSON parsing fails
        assert isinstance(result["body"], str)
