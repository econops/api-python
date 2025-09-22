#!/usr/bin/env python3
"""
Example demonstrating the new credentials functionality in the Econops client.

This shows how to save credentials to a file and then use them automatically.
"""

from econops import Client, setup_credentials

def main():
    # Method 1: Save credentials using the convenience function
    print("Setting up credentials for user 'demo_user'...")
    setup_credentials("demo_user", "demo_token_123")
    
    # Method 2: Save credentials using the client instance
    print("Setting up credentials for user 'test_user'...")
    client = Client(token="test_token_456")
    client.save_credentials("test_user", "test_token_456")
    
    # Now use the credentials without explicitly providing tokens
    print("\nCreating clients using saved credentials...")
    
    # This will automatically load the token from ~/.econops/credentials/demo_user.id
    demo_client = Client(id="demo_user")
    print(f"Demo client token: {demo_client.token}")
    
    # This will automatically load the token from ~/.econops/credentials/test_user.id
    test_client = Client(id="test_user")
    print(f"Test client token: {test_client.token}")
    
    # You can still override with explicit tokens
    override_client = Client(id="demo_user", token="override_token")
    print(f"Override client token: {override_client.token}")
    
    print("\n✅ Credentials saved and loaded successfully!")
    print("Files created:")
    print("  ~/.econops/credentials/demo_user.id")
    print("  ~/.econops/credentials/test_user.id")

if __name__ == "__main__":
    main()













