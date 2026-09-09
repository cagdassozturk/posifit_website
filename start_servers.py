#!/usr/bin/env python3
"""
Startup script to run both Flask (static) and Dash (data) servers
"""
import subprocess
import time
import sys
import os

def start_servers():
    """Start both Flask and Dash servers"""
    print("🚀 Starting POSIFIT servers...")
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Start Dash server (data pages) on port 8051
        print("📊 Starting Dash server (data pages) on port 8051...")
        dash_process = subprocess.Popen([
            sys.executable, "dash_app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for Dash to start
        time.sleep(3)
        
        # Start Flask server (static pages) on port 8050  
        print("🌐 Starting Flask server (static pages) on port 8050...")
        flask_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("\n✅ Servers started successfully!")
        print("📱 Access your website at: http://localhost:8050")
        print("🔗 Static pages: http://localhost:8050/")
        print("📊 Data explorer: http://localhost:8050/pilot_lux_explorer")
        print("⚡ Optimized results: http://localhost:8050/pilot_lux_optimized")
        print("\n🎨 Navigation: Now using your friend's unified navbar across all pages!")
        print("\n⚠️  Press Ctrl+C to stop both servers")
        
        # Keep both processes running
        try:
            dash_process.wait()
            flask_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            dash_process.terminate()
            flask_process.terminate()
            print("✅ Servers stopped")
            
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_servers()
