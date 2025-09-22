"""
Econops API Client

This module provides the main Client class for interacting with the Econops API.
"""

import os
import requests
import json
import hashlib
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from starlette.middleware.sessions import SessionMiddleware





def callsignature(route: str, request_data: dict, pregiven: Optional[str] = None) -> str:
    """
    Generate a unique signature for route and request data.
    Args:
        route: The API route (e.g., "/compute/pca")
        request_data: The JSON request data as a dictionary
        pregiven: If not None, return this value directly (for caching/pre-computed signatures)
    
    Returns:
        A unique hash string representing the route and request data
    """
    if pregiven is not None:
        return pregiven
    
    # Create a deterministic string representation of the data
    # Sort the request data to ensure consistent hashing regardless of key order
    sorted_data = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
    
    # Hash the route for flexibility while maintaining security
    route_hash = hashlib.sha256(route.encode('utf-8')).hexdigest()[:8]  # First 8 chars
    
    # Combine route hash and data hash
    signature = route_hash + hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()
    return signature


def get_cache_dir() -> Path:
    """Get the cache directory for storing API responses."""
    cache_dir = Path.home() / ".econops" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cached_response(signature: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached response for a given signature.
    
    Args:
        signature: The request signature to look up
        
    Returns:
        Cached response data or None if not found
    """
    cache_file = get_cache_dir() / f"{signature}.pkl"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Check if cache is still valid (optional: add expiration logic)
            return cached_data
        except (pickle.PickleError, EOFError):
            # Corrupted cache file, remove it
            cache_file.unlink(missing_ok=True)
    
    return None


def cache_response(signature: str, response_data: Dict[str, Any]) -> None:
    """
    Cache a response for future use.
    
    Args:
        signature: The request signature as cache key
        response_data: The response data to cache
    """
    cache_file = get_cache_dir() / f"{signature}.pkl"
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(response_data, f)
    except (IOError, OSError):
        # Silently fail if we can't write to cache
        pass


class Client:
    """
    Econops API Client
    
    A client for making requests to the Econops API with automatic authentication
    and request signing.
    
    Args:
        token (str, optional): API token. If not provided, will try to get from
            'ECONOPS_TOKEN' environment variable.
        base_url (str, optional): Base URL for the API. Defaults to 
            "https://api.econops.com".
        use_cache (bool, optional): Whether to use response caching. Defaults to True.
        use_certificate (bool, optional): Whether to verify SSL certificates. Defaults to False.
    """
    
    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.econops.com", 
                 use_cache: bool = True, use_certificate: bool = False):
        # Get token from parameter or environment
        self.token = token or os.environ.get('ECONOPS_TOKEN', 'demo')
        if not self.token:
            raise ValueError("Token not provided and 'ECONOPS_TOKEN' environment variable not found")
        
        self.base_url = base_url.rstrip('/')
        self.use_cache = use_cache
        self.use_certificate = use_certificate
        self.version = "0.1.0"
        
        # Prepare default headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.dims = {}

    def set_dim(self, **kwargs):
        self.dims.update(kwargs)

    def add_dim(self, **kwargs):
        # get key
        key = list(kwargs.keys())[0]
        value = kwargs[key]
        if key in self.dims:
            if isinstance(self.dims[key], list):
                self.dims[key].append(value)
            else:
                self.dims[key] = [self.dims[key], value]
        else:
            self.dims[key] = value

    def get_dims(self):
        return self.dims
    
    def get(self, route: str) -> requests.Response:
        """
        Make a GET request to any endpoint.

        Args:
            route (str): The API route to call (e.g., "/health", "/test-simple")
        
        Returns:
            requests.Response: The response from the API
            
        Example:
            client.get("/health")
        """
        # Generate signature for the request
        signature = callsignature(route, {})
        
        # Prepare headers with signature
        headers = self.headers.copy()
        headers["X-Signature"] = signature
        
        # Make actual GET request
        url = urljoin(self.base_url, route)
        response = requests.get(url=url, headers=headers, verify=self.use_certificate)
        
        # Display timing information using built-in requests metadata
        try:
            elapsed = response.elapsed.total_seconds()
            print(f"[GET] {route} - {elapsed:.4f}s")
        except (AttributeError, TypeError):
            # Skip timing display for mocked responses in tests
            pass
        
        return response
    
    
    def delete(self, route: str) -> requests.Response:
        """
        Delete resources.
        
        Args:
            route (str): The API route to call (e.g., "/cache", "/user/123")
        
        Returns:
            requests.Response: The response from the API
            
        Example:
            client.delete("/cache")
        """
        # Generate signature for the request
        signature = callsignature(route, {})
        
        # Prepare headers with signature
        headers = self.headers.copy()
        headers["X-Signature"] = signature
        
        # Make API request with signature
        url = urljoin(self.base_url, route)
        response = requests.delete(url, headers=headers, verify=self.use_certificate)
        
        # Display timing information using built-in requests metadata
        try:
            elapsed = response.elapsed.total_seconds()
            print(f"[DELETE] {route} - {elapsed:.4f}s")
        except (AttributeError, TypeError):
            # Skip timing display for mocked responses in tests
            pass
        
        return response
    
    
    def post(self, route: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        POST data to any endpoint.
        
        Args:
            route (str): The API route to call
            data (dict, optional): Data to send with the request
        
        Returns:
            requests.Response: The response from the API
        """
        # Generate signature for the request
        signature = callsignature(route, data or {})
        
        # Prepare headers with signature
        headers = self.headers.copy()
        headers["X-Signature"] = signature
        
        # Make API request with signature
        url = urljoin(self.base_url, route)
        json = {"payload": (data or {}).copy()}
        
        response = requests.post(url, json=json, headers=headers, verify=self.use_certificate)
        # Display timing information using built-in requests metadata
        try:
            elapsed = response.elapsed.total_seconds()
            print(f"[POST] {route} - {elapsed:.4f}s")
        except (AttributeError, TypeError):
            # Skip timing display for mocked responses in tests
            pass
        return response
    

    def put(self, route: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        PUT (update/replace) data to any endpoint.
        
        Args:
            route (str): The API route to call
            data (dict, optional): Data to send with the request
        
        Returns:
            requests.Response: The response from the API
        """
        # Generate signature for the request
        signature = callsignature(route, data or {})
        
        # Prepare headers with signature
        headers = self.headers.copy()
        headers["X-Signature"] = signature
        
        # Make API request with signature
        url = urljoin(self.base_url, route)
        payload = {"payload": (data or {}).copy()}
        
        response = requests.put(url, json=payload, headers=headers, verify=self.use_certificate)
        
        # Display timing information using built-in requests metadata
        try:
            elapsed = response.elapsed.total_seconds()
            print(f"[PUT] {route} - {elapsed:.4f}s")
        except (AttributeError, TypeError):
            # Skip timing display for mocked responses in tests
            pass
        
        return response
    

    def patch(self, route: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        PATCH (partial update) data to any endpoint.
        
        Args:
            route (str): The API route to call
            data (dict, optional): Data to send with the request
        
        Returns:
            requests.Response: The response from the API
        """
        # Generate signature for the request
        signature = callsignature(route, data or {})
        
        # Prepare headers with signature
        headers = self.headers.copy()
        headers["X-Signature"] = signature
        
        # Make API request with signature
        url = urljoin(self.base_url, route)
        payload = {"payload": (data or {}).copy()}
        
        response = requests.patch(url, json=payload, headers=headers, verify=self.use_certificate)
        
        # Display timing information using built-in requests metadata
        try:
            elapsed = response.elapsed.total_seconds()
            print(f"[PATCH] {route} - {elapsed:.4f}s")
        except (AttributeError, TypeError):
            # Skip timing display for mocked responses in tests
            pass
        
        return response
    
    def create(self, route: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Create a new resource (convenience method that uses POST).
        
        Args:
            route (str): The API route to call
            data (dict, optional): Data to send with the request
        
        Returns:
            requests.Response: The response from the API
            
        Example:
            client.create("/api/openai", {"token": "sk-123...", "description": "OpenAI key"})
        """
        return self.post(route, data)
    
    def clear_cache(self) -> None:
        """Clear all cached responses."""
        cache_dir = get_cache_dir()
        for cache_file in cache_dir.glob("*.pkl"):
            cache_file.unlink(missing_ok=True)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache."""
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.pkl"))
        
        return {
            "cache_directory": str(cache_dir),
            "cached_requests": len(cache_files),
            "cache_size_bytes": sum(f.stat().st_size for f in cache_files if f.exists())
        }
    
    def generate_ed25519_keys(self, api_name: str = "challenge_response") -> Dict[str, str]:
        """
        Generate Ed25519 key pair for challenge-response API authentication.
        
        This method creates the SSH key pair needed for APIs that use Ed25519-based
        challenge-response authentication (like Nordnet, some trading APIs, etc.).
        
        Args:
            api_name: Name of the API for customizing instructions
            
        Returns:
            dict: Contains 'private_key', 'public_key', and setup instructions
            
        Example:
            keys = client.generate_ed25519_keys("nordnet")
            print("Public key to upload:")
            print(keys['public_key'])
        """
        try:
            import subprocess
            import tempfile
            
            # Create temporary directory for key generation
            with tempfile.TemporaryDirectory() as temp_dir:
                private_key_path = os.path.join(temp_dir, "id_ed25519")
                public_key_path = os.path.join(temp_dir, "id_ed25519.pub")
                
                # Generate Ed25519 key pair using ssh-keygen
                cmd = [
                    "ssh-keygen", 
                    "-t", "ed25519", 
                    "-a", "150",
                    "-f", private_key_path,
                    "-N", ""  # No passphrase
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Read the generated keys
                with open(private_key_path, 'r') as f:
                    private_key = f.read().strip()
                
                with open(public_key_path, 'r') as f:
                    public_key = f.read().strip()
                
                # Generate API-specific instructions
                instructions = self._get_challenge_response_instructions(api_name)
                
                return {
                    "private_key": private_key,
                    "public_key": public_key,
                    "api_name": api_name,
                    "instructions": instructions,
                    "store_command": f"client.post('/api/{api_name}', {{'auth_method': 'challenge_response', 'private_key': '...', 'public_key': '...'}})"
                }
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to generate SSH keys: {e.stderr}")
        except FileNotFoundError:
            raise Exception("ssh-keygen not found. Please install OpenSSH or use a system with SSH key generation capabilities.")
        except Exception as e:
            raise Exception(f"Error generating Ed25519 keys: {str(e)}")
    
    def _get_challenge_response_instructions(self, api_name: str) -> List[str]:
        """
        Get API-specific instructions for challenge-response setup.
        
        Args:
            api_name: Name of the API
            
        Returns:
            List of instruction steps
        """
        instructions_map = {
            "nordnet": [
                "1. Copy the public_key content above",
                "2. Go to Nordnet web interface: My pages -> Settings -> My profile -> Security -> API key",
                "3. Click 'Add a new API key' and paste the public key",
                "4. Copy the API key UUID that Nordnet provides",
                "5. Store the private key using the store_command below"
            ],
            "trading_api": [
                "1. Copy the public_key content above",
                "2. Go to your trading platform's API settings",
                "3. Upload the public key in the designated field",
                "4. Note any API key or identifier provided",
                "5. Store the private key using the store_command below"
            ],
            "generic": [
                "1. Copy the public_key content above",
                "2. Upload the public key to your API provider's web interface",
                "3. Note any API key, UUID, or identifier provided",
                "4. Store the private key using the store_command below"
            ]
        }
        
        return instructions_map.get(api_name.lower(), instructions_map["generic"])