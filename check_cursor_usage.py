#!/usr/bin/env python3
"""
Script to check Cursor token usage for a team member using the Cursor Admin API.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Cursor Admin API base URL
CURSOR_API_BASE = "https://api.cursor.com"

def load_credentials() -> Optional[str]:
    """Load Cursor API credentials from various sources."""
    # Check environment variable first
    api_key = os.getenv("CURSOR_API_KEY")
    if api_key:
        return api_key
    
    # Check for .env file in current and parent directories
    env_files = [".env", ".env.local", "venve/.env", "venv/.env", "../.env", "../venve/.env"]
    for env_file in env_files:
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("CURSOR_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception as e:
                print(f"Error reading {env_file}: {e}")
    
    # Check for credentials.json or config.json
    cred_files = ["credentials.json", "config.json", "cursor_credentials.json", 
                  "venve/credentials.json", "venv/credentials.json",
                  "../credentials.json", "../venve/credentials.json"]
    for cred_file in cred_files:
        if os.path.exists(cred_file):
            try:
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                    if "CURSOR_API_KEY" in data:
                        return data["CURSOR_API_KEY"]
                    if "cursor_api_key" in data:
                        return data["cursor_api_key"]
                    if "api_key" in data:
                        return data["api_key"]
            except Exception as e:
                print(f"Error reading {cred_file}: {e}")
    
    return None

def make_api_request(endpoint: str, api_key: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to the Cursor Admin API."""
    url = f"{CURSOR_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Authentication failed. Please check your API key.")
        elif e.response.status_code == 403:
            print("Error: Access forbidden. You may not have admin permissions.")
        else:
            print(f"Error: HTTP {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        sys.exit(1)

def get_team_members(api_key: str) -> list:
    """Get all team members."""
    print("Fetching team members...")
    data = make_api_request("/v1/team/members", api_key)
    return data.get("members", data) if isinstance(data, dict) else data

def find_user_by_name(members: list, name: str) -> Optional[Dict]:
    """Find a user by name (case-insensitive partial match)."""
    name_lower = name.lower()
    for member in members:
        member_name = member.get("name", "").lower()
        member_email = member.get("email", "").lower()
        if name_lower in member_name or name_lower in member_email:
            return member
    return None

def get_daily_usage(api_key: str, start_date: datetime, end_date: datetime, user_id: Optional[str] = None) -> Dict:
    """Get daily usage data."""
    params = {
        "startDate": int(start_date.timestamp() * 1000),  # epoch milliseconds
        "endDate": int(end_date.timestamp() * 1000)
    }
    if user_id:
        params["userId"] = user_id
    
    print(f"Fetching usage data from {start_date.date()} to {end_date.date()}...")
    return make_api_request("/v1/usage/daily", api_key, params)

def get_spend_data(api_key: str, start_date: datetime, end_date: datetime, email: Optional[str] = None) -> Dict:
    """Get spending data."""
    params = {
        "startDate": int(start_date.timestamp() * 1000),
        "endDate": int(end_date.timestamp() * 1000)
    }
    if email:
        params["email"] = email
    
    print(f"Fetching spending data from {start_date.date()} to {end_date.date()}...")
    return make_api_request("/v1/spend", api_key, params)

def get_usage_events(api_key: str, start_date: datetime, end_date: datetime, 
                     email: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
    """Get usage events data."""
    params = {
        "startDate": int(start_date.timestamp() * 1000),
        "endDate": int(end_date.timestamp() * 1000),
        "page": 1,
        "pageSize": 1000
    }
    if email:
        params["email"] = email
    if user_id:
        params["userId"] = user_id
    
    print(f"Fetching usage events from {start_date.date()} to {end_date.date()}...")
    return make_api_request("/v1/usage/events", api_key, params)

def format_number(num: Any) -> str:
    """Format numbers for display."""
    if num is None:
        return "0"
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

def main():
    """Main function to check token usage for Srivatsan."""
    print("=" * 60)
    print("Cursor Team Member Token Usage Checker")
    print("=" * 60)
    print()
    
    # Check for API key in command line arguments
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        if api_key.startswith("--help") or api_key.startswith("-h"):
            print("Usage: python check_cursor_usage.py [API_KEY]")
            print("\nThe API key can be provided as:")
            print("  1. Command line argument")
            print("  2. CURSOR_API_KEY environment variable")
            print("  3. .env file with CURSOR_API_KEY=your_key")
            print("  4. credentials.json file")
            print("\nTo get your API key:")
            print("  1. Go to cursor.com/dashboard")
            print("  2. Navigate to Settings -> Cursor Admin API Keys")
            print("  3. Create a new API key")
            sys.exit(0)
    
    # Load API key from other sources if not provided
    if not api_key:
        api_key = load_credentials()
    
    if not api_key:
        print("Error: Cursor API key not found.")
        print("\nPlease provide your API key in one of these ways:")
        print("1. Set CURSOR_API_KEY environment variable")
        print("2. Create a .env file with CURSOR_API_KEY=your_key")
        print("3. Create credentials.json with CURSOR_API_KEY field")
        print("\nTo get your API key:")
        print("1. Go to cursor.com/dashboard")
        print("2. Navigate to Settings -> Cursor Admin API Keys")
        print("3. Create a new API key")
        sys.exit(1)
    
    # Get team members
    members = get_team_members(api_key)
    if not members:
        print("No team members found or unable to fetch members.")
        sys.exit(1)
    
    print(f"Found {len(members)} team member(s)")
    print()
    
    # Find Srivatsan
    user = find_user_by_name(members, "Srivatsan")
    if not user:
        print("User 'Srivatsan' not found in team members.")
        print("\nAvailable team members:")
        for member in members:
            print(f"  - {member.get('name', 'Unknown')} ({member.get('email', 'No email')})")
        sys.exit(1)
    
    print(f"Found user: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
    print(f"User ID: {user.get('id', 'Unknown')}")
    print(f"Role: {user.get('role', 'Unknown')}")
    
    # Check if using team license
    is_team_member = user.get('role') in ['admin', 'member', 'viewer'] or 'team' in str(user.get('subscription', '')).lower()
    license_type = "Team License" if is_team_member else "Personal License"
    print(f"License Type: {license_type}")
    print()
    
    # Get usage data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    user_id = user.get('id')
    user_email = user.get('email')
    
    # Get daily usage
    daily_usage = get_daily_usage(api_key, start_date, end_date, user_id)
    
    # Get spending data
    spend_data = get_spend_data(api_key, start_date, end_date, user_email)
    
    # Get usage events for token details
    usage_events = get_usage_events(api_key, start_date, end_date, user_email, user_id)
    
    # Display results
    print()
    print("=" * 60)
    print("TOKEN USAGE SUMMARY (Last 30 Days)")
    print("=" * 60)
    print()
    
    # Process daily usage data
    if isinstance(daily_usage, list):
        total_requests = sum(day.get('subscriptionIncludedReqs', 0) + 
                           day.get('apiKeyReqs', 0) + 
                           day.get('usageBasedReqs', 0) 
                           for day in daily_usage if isinstance(day, dict))
        
        total_lines_added = sum(day.get('chatAcceptedLinesAdded', 0) 
                               for day in daily_usage if isinstance(day, dict))
        
        total_tabs = sum(day.get('tabsAccepted', 0) 
                        for day in daily_usage if isinstance(day, dict))
        
        print(f"Total Requests: {format_number(total_requests)}")
        print(f"  - Subscription Included: {format_number(sum(day.get('subscriptionIncludedReqs', 0) for day in daily_usage if isinstance(day, dict)))}")
        print(f"  - API Key Requests: {format_number(sum(day.get('apiKeyReqs', 0) for day in daily_usage if isinstance(day, dict)))}")
        print(f"  - Usage-Based: {format_number(sum(day.get('usageBasedReqs', 0) for day in daily_usage if isinstance(day, dict)))}")
        print()
        print(f"Total Lines Added: {format_number(total_lines_added)}")
        print(f"Total Tabs Accepted: {format_number(total_tabs)}")
    
    # Process spending data
    if isinstance(spend_data, dict):
        total_spend = spend_data.get('total', spend_data.get('totalCents', 0))
        if total_spend:
            print(f"\nTotal Spending: ${total_spend / 100:.2f}" if total_spend > 100 else f"Total Spending: {total_spend} cents")
    
    # Process usage events for token consumption
    if isinstance(usage_events, dict):
        events = usage_events.get('events', usage_events.get('data', []))
        if isinstance(events, list):
            total_tokens = sum(event.get('tokensConsumed', 0) 
                             for event in events if isinstance(event, dict))
            print(f"\nTotal Tokens Consumed: {format_number(total_tokens)}")
            
            # Group by model
            model_usage = {}
            for event in events:
                if isinstance(event, dict):
                    model = event.get('model', 'Unknown')
                    tokens = event.get('tokensConsumed', 0)
                    model_usage[model] = model_usage.get(model, 0) + tokens
            
            if model_usage:
                print("\nToken Usage by Model:")
                for model, tokens in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
                    print(f"  - {model}: {format_number(tokens)} tokens")
    
    print()
    print("=" * 60)
    print(f"License Status: {license_type}")
    print("=" * 60)

if __name__ == "__main__":
    main()
