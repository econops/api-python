"""
Tests for the EconOps API client.
"""

import pytest
from unittest.mock import patch, Mock
from econops.client import Client, callsignature


class TestCallSignature:
    """Test the callsignature function."""
    
    def test_callsignature_basic(self):
        """Test basic signature generation."""
        route = "/compute/pca"
        data = {"data": [[1, 2, 3]], "n_components": 2}
        
        signature = callsignature(route, data)
        
        assert isinstance(signature, str)
    
    def test_callsignature_deterministic(self):
        """Test that same input produces same signature."""
        route = "/test"
        data = {"key": "value"}
        
        sig1 = callsignature(route, data)
        sig2 = callsignature(route, data)
        
        assert sig1 == sig2
    
    def test_callsignature_pregiven(self):
        """Test pregiven signature override."""
        route = "/test"
        data = {"key": "value"}
        pregiven = "test_signature"
        
        signature = callsignature(route, data, pregiven)
        
        assert signature == pregiven
    
    def test_callsignature_route_dependent(self):
        """Test that signatures are dependent on route."""
        data = {"data": [[1, 2, 3]], "n_components": 2}
        
        # Same data, different routes should produce different signatures
        sig1 = callsignature("/compute/pca", data)
        sig2 = callsignature("/api/v2/pca", data)
        
        assert sig1 != sig2  # Different routes = different signatures


class TestClient:
    """Test the Client class."""
    
    def test_client_init_with_token(self):
        """Test client initialization with token."""
        client = Client(token="test_token")
        
        assert client.token == "test_token"
        assert client.base_url == "https://api.econops.com"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test_token"
    
    def test_client_init_without_token(self):
        """Test client initialization without token (should use demo)."""
        with patch.dict('os.environ', {}, clear=True):
            client = Client()
            
            assert client.token == "demo"
    
    def test_client_init_with_base_url(self):
        """Test client initialization with custom base URL."""
        client = Client(token="test", base_url="https://custom.com")
        
        assert client.base_url == "https://custom.com"
    
    def test_client_init_with_base_url_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = Client(token="test", base_url="https://custom.com/")
        
        assert client.base_url == "https://custom.com"
    
    @patch('requests.post')
    def test_get_post(self, mock_post):
        """Test POST request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = Client(token="test_token")
        response = client.get("/test", {"data": "value"})
        
        assert response == mock_response
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_get_get(self, mock_get):
        """Test GET request without data (no signature needed)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = Client(token="test_token")
        response = client.get("/test", method="GET")
        
        assert response == mock_response
        mock_get.assert_called_once()
        
        # Check that no signature was added to URL
        call_args = mock_get.call_args
        url = call_args[0][0]  # First positional argument is URL
        assert "signature=" not in url
    
    def test_get_signature_in_payload(self):
        """Test that signature is added to request payload."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            client = Client(token="test_token")
            client.get("/test", {"data": "value"})
            
            # Check that the call was made with signature in payload
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert "signature" in payload
            assert isinstance(payload["signature"], str)
            assert len(payload["signature"]) == 72  # 8 chars route hash + 64 chars data hash
            assert payload["data"] == "value"
    
    def test_get_with_data_forces_post(self):
        """Test that GET requests with data are converted to POST."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            client = Client(token="test_token")
            # This should be converted to POST even though method="GET"
            client.get("/test", {"data": "value"}, method="GET")
            
            # Should have called POST, not GET
            mock_post.assert_called_once() 