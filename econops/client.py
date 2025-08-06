"""
Econops API Client

This module provides the main Client class for interacting with the Econops API.
"""

import os
import requests
import json
import hashlib
from typing import Optional, Dict, Any


def callsignature(route: str, request_data: dict, pregiven: Optional[str] = None) -> str:
    """
    Generate a unique signature for a route call with specific JSON request data.
    
    Args:
        route: The API route (e.g., "/compute/pca")
        request_data: The JSON request data as a dictionary
        pregiven: If not None, return this value directly (for caching/pre-computed signatures)
    
    Returns:
        A unique hash string representing the route and request data combination
    """
    if pregiven is not None:
        return pregiven
    
    # Create a deterministic string representation of the route and data
    # Sort the request data to ensure consistent hashing regardless of key order
    sorted_data = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
    
    # Combine route and data
    signature_input = f"{route}:{sorted_data}"
    
    # Generate SHA-256 hash
    signature = hashlib.sha256(signature_input.encode('utf-8')).hexdigest()
    
    return signature


class Client:
    """
    EconOps API Client
    
    A client for making requests to the EconOps API with automatic authentication
    and request signing.
    
    Args:
        token (str, optional): API token. If not provided, will try to get from
            'econops_token' environment variable.
        base_url (str, optional): Base URL for the API. Defaults to 
            "http://econops.com:8000".
    """
    
    def __init__(self, token: Optional[str] = None, base_url: str = "https://econops.com:8000"):
        # Get token from parameter or environment
        self.token = token or os.environ.get('econops_token', 'demo')
        if not self.token:
            raise ValueError("Token not provided and 'econops_token' environment variable not found")
        
        self.base_url = base_url.rstrip('/')
        
        # Prepare default headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, route: str, data: Optional[Dict[str, Any]] = None, 
                    method: str = "POST") -> requests.Response:
        """
        Make a request to any route with bearer token authentication.
        
        Args:
            route (str): The API route to call (e.g., "/compute/pca")
            data (dict, optional): Data to send in the request body
            method (str): HTTP method (GET, POST, etc.)
        
        Returns:
            requests.Response: The response from the API
        """
        url = f"{self.base_url}{route}"
        
        # Generate signature for the request
        request_data = data or {}
        signature = callsignature(route, request_data)
        
        # Add signature to headers
        request_headers = self.headers.copy()
        request_headers["computation-signature"] = signature
        
        if method.upper() == "GET":
            response = requests.get(url, headers=request_headers, verify=False)
        else:
            response = requests.post(url, headers=request_headers, json=data, verify=False)
        
        return response 