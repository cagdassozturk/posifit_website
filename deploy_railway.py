#!/usr/bin/env python3
"""
Railway deployment helper script
This script helps prepare your code for Railway deployment
"""
import os
import re

def update_urls_for_production(base_url):
    """Update hardcoded localhost URLs to production URLs"""
    
    # Files that need URL updates
    files_to_update = [
        'dash_app.py',
        'main.py'
    ]
    
    for filename in files_to_update:
        if os.path.exists(filename):
            print(f"📝 Updating URLs in {filename}...")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace localhost URLs with production URL
            content = content.replace('http://localhost:8050', base_url)
            content = content.replace('http://localhost:8051', base_url)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {filename}")
        else:
            print(f"⚠️  File {filename} not found")

def create_railway_config():
    """Create Railway configuration files"""
    
    # Create railway.json
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python start_servers_production.py",
            "healthcheckPath": "/",
            "healthcheckTimeout": 100,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    import json
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Created railway.json")

def main():
    """Main deployment preparation"""
    print("🚀 Preparing POSIFIT for Railway deployment...")
    
    # Get production URL from user
    production_url = input("Enter your production URL (e.g., https://your-app.railway.app): ").strip()
    
    if not production_url:
        print("❌ Production URL is required!")
        return
    
    if not production_url.startswith('http'):
        production_url = f"https://{production_url}"
    
    print(f"🌐 Using production URL: {production_url}")
    
    # Update URLs
    update_urls_for_production(production_url)
    
    # Create Railway config
    create_railway_config()
    
    print("\n✅ Deployment preparation complete!")
    print("\n📋 Next steps:")
    print("1. Push your code to GitHub")
    print("2. Go to https://railway.app")
    print("3. Create new project from GitHub")
    print("4. Select your repository")
    print("5. Railway will automatically deploy!")
    
    print(f"\n🔗 Your site will be available at: {production_url}")

if __name__ == "__main__":
    main()
