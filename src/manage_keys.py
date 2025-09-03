"""
API Key Management CLI Tool
"""
import argparse
import sys
import json
from datetime import datetime
from .auth import APIKeyManager

def main():
    parser = argparse.ArgumentParser(description='ImageMagick API Key Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate API key command
    generate_parser = subparsers.add_parser('generate', help='Generate a new API key')
    generate_parser.add_argument('name', help='Name for the API key')
    generate_parser.add_argument('--permissions', nargs='+', 
                               default=['process', 'health'],
                               help='Permissions for the API key')
    generate_parser.add_argument('--expires-days', type=int,
                               help='Days until expiration')
    
    # List API keys command
    list_parser = subparsers.add_parser('list', help='List all API keys')
    
    # Revoke API key command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke an API key')
    revoke_parser.add_argument('key_id', help='Key ID to revoke')
    
    # Show API key details command
    show_parser = subparsers.add_parser('show', help='Show API key details')
    show_parser.add_argument('key_id', help='Key ID to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize API key manager
    manager = APIKeyManager()
    
    if args.command == 'generate':
        key_info = manager.generate_api_key(
            name=args.name,
            permissions=args.permissions,
            expires_days=args.expires_days
        )
        
        print("✅ API Key Generated Successfully!")
        print("=" * 50)
        print(f"Name: {key_info['name']}")
        print(f"Key ID: {key_info['key_id']}")
        print(f"API Key: {key_info['api_key']}")
        print(f"Permissions: {', '.join(key_info['permissions'])}")
        if key_info['expires_at']:
            print(f"Expires: {key_info['expires_at']}")
        print("=" * 50)
        print("⚠️  IMPORTANT: Save this API key securely. It cannot be retrieved again!")
        print("📋 Usage: Include this key in the 'X-API-Key' header for API requests")
        
    elif args.command == 'list':
        keys = manager.list_api_keys()
        
        if not keys:
            print("No API keys found.")
            return
        
        print("📋 API Keys:")
        print("=" * 80)
        print(f"{'ID':<16} {'Name':<20} {'Status':<8} {'Usage':<8} {'Last Used':<20}")
        print("-" * 80)
        
        for key in keys:
            status = "Active" if key['active'] else "Revoked"
            last_used = key['last_used']
            if last_used:
                if isinstance(last_used, str):
                    last_used = datetime.fromisoformat(last_used).strftime('%Y-%m-%d %H:%M')
                else:
                    last_used = last_used.strftime('%Y-%m-%d %H:%M')
            else:
                last_used = "Never"
            
            print(f"{key['key_id']:<16} {key['name']:<20} {status:<8} {key['usage_count']:<8} {last_used:<20}")
    
    elif args.command == 'revoke':
        if manager.revoke_api_key(args.key_id):
            print(f"✅ API key {args.key_id} has been revoked.")
        else:
            print(f"❌ API key {args.key_id} not found.")
    
    elif args.command == 'show':
        keys = manager.list_api_keys()
        key = next((k for k in keys if k['key_id'] == args.key_id), None)
        
        if not key:
            print(f"❌ API key {args.key_id} not found.")
            return
        
        print(f"📋 API Key Details: {args.key_id}")
        print("=" * 50)
        print(f"Name: {key['name']}")
        print(f"Status: {'Active' if key['active'] else 'Revoked'}")
        print(f"Permissions: {', '.join(key['permissions'])}")
        print(f"Created: {key['created_at']}")
        if key['expires_at']:
            print(f"Expires: {key['expires_at']}")
        print(f"Usage Count: {key['usage_count']}")
        if key['last_used']:
            print(f"Last Used: {key['last_used']}")

if __name__ == '__main__':
    main()
