"""
Command-line interface for the EconOps API client.
"""

import argparse
import json
import sys
from typing import Dict, Any

from .client import Client


def main():
    """
    Main CLI entry point for the Econops API client.
    """
    parser = argparse.ArgumentParser(
        description="Econops API Client - Statistical and data science API for economics and finance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Make a PCA request
  econops --route /compute/pca --data '{"data": [[1,2,3], [4,5,6]], "n_components": 2}'
  
  # Make a GET request
  econops --route /status --method GET
  
  # Use environment variable for token
  export econops_token="your_token"
  econops --route /compute/pca --data '{"data": [[1,2,3]]}'
        """
    )
    
    parser.add_argument(
        "--route", 
        required=True,
        help="API route to call (e.g., /compute/pca)"
    )
    
    parser.add_argument(
        "--data", 
        type=str,
        help="JSON data to send in request body"
    )
    
    parser.add_argument(
        "--method", 
        default="POST",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method (default: POST)"
    )
    
    parser.add_argument(
        "--token",
        help="API token (or set econops_token environment variable)"
    )
    
    parser.add_argument(
        "--base-url",
        default="https://api.econops.com",
        help="Base URL for the API (default: https://api.econops.com)"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON response"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable response caching"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse JSON data if provided
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON data: {e}", file=sys.stderr)
                sys.exit(1)
        
        # Initialize client
        client = Client(token=args.token, base_url=args.base_url, use_cache=not args.no_cache)
        
        # Make request
        if args.method == "GET":
            response = client.get(args.route)
        elif args.method == "POST":
            response = client.post(args.route, data=data)
        elif args.method == "PUT":
            response = client.put(args.route, data=data)
        elif args.method == "DELETE":
            response = client.delete(args.route)
        else:
            print(f"Unsupported method: {args.method}", file=sys.stderr)
            sys.exit(1)
        
        # Print response
        if response.status_code == 200:
            try:
                result = response.json()
                if args.pretty:
                    print(json.dumps(result, indent=2))
                else:
                    print(json.dumps(result))
            except json.JSONDecodeError:
                print(response.text)
        else:
            print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 