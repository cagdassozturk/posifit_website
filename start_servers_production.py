#!/usr/bin/env python3
"""
Production startup script for POSIFIT servers
Handles environment variables and production settings
"""
import subprocess
import time
import sys
import os
from threading import Thread

def start_dash_server():
    """Start Dash server in a separate thread"""
    try:
        print("📊 Starting Dash server (data pages)...")
        subprocess.run([sys.executable, "dash_app.py"], check=True)
    except Exception as e:
        print(f"❌ Error starting Dash server: {e}")

def start_flask_server():
    """Start Flask server in a separate thread"""
    try:
        print("🌐 Starting Flask server (static pages)...")
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")

def start_servers():
    """Start both Flask and Dash servers"""
    print("🚀 Starting POSIFIT servers...")
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Get port from environment variable (for production)
    flask_port = os.environ.get('PORT', '8050')
    dash_port = os.environ.get('DASH_PORT', '8051')
    
    print(f"🌐 Flask server will run on port {flask_port}")
    print(f"📊 Dash server will run on port {dash_port}")
    
    try:
        # Start Dash server in a separate thread
        dash_thread = Thread(target=start_dash_server, daemon=True)
        dash_thread.start()
        
        # Wait a moment for Dash to start
        time.sleep(3)
        
        # Start Flask server (this will be the main process)
        print("🌐 Starting Flask server (static pages)...")
        subprocess.run([sys.executable, "main.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        print("✅ Servers stopped")
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_servers()
