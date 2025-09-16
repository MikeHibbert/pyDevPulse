#!/usr/bin/env python3
"""
Fixed startup script for DevPulse container that uses the working database solution.
This script starts both the WebSocket server and the fixed API server.
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '/app')

async def start_websocket_server():
    """Start the WebSocket server on port 8008"""
    try:
        from devpulse.websocket import start_websocket_server
        print("Starting WebSocket server on port 8008...")
        await start_websocket_server(host='0.0.0.0', port=8008)
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")
        # Continue running even if WebSocket fails

async def start_api_server():
    """Start the fixed API server on port 8088"""
    try:
        print("Starting fixed API server on port 8088...")
        # Set environment variable for the API server
        os.environ['DEVPULSE_DB_URL'] = 'sqlite:///app/data/devpulse.db'
        
        # Import and run the fixed API server
        import uvicorn
        from devpulse_api_server import app
        
        config = uvicorn.Config(
            app=app,
            host='0.0.0.0',
            port=8088,
            log_level='info'
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        print(f"Error starting API server: {e}")
        # Fallback to subprocess if direct import fails
        try:
            print("Falling back to subprocess for API server...")
            process = subprocess.Popen([
                sys.executable, '/app/devpulse_api_server.py'
            ], env=dict(os.environ, DEVPULSE_DB_URL='sqlite:///app/data/devpulse.db'))
            
            # Keep the process running
            while True:
                if process.poll() is not None:
                    print("API server process ended, restarting...")
                    process = subprocess.Popen([
                        sys.executable, '/app/devpulse_api_server.py'
                    ], env=dict(os.environ, DEVPULSE_DB_URL='sqlite:///app/data/devpulse.db'))
                await asyncio.sleep(5)
        except Exception as e2:
            print(f"Fallback also failed: {e2}")

async def main():
    """Main function to start both servers"""
    print("Starting DevPulse servers with fixed database access...")
    
    # Ensure data directory exists
    data_dir = Path('/app/data')
    data_dir.mkdir(exist_ok=True)
    
    # Initialize DevPulse if needed
    try:
        from devpulse import init
        db_url = os.getenv('DEVPULSE_DB_URL', 'sqlite:///app/data/devpulse.db')
        init(
            websocket_url='ws://localhost:8008',
            enable_db_logging=True,
            db_url=db_url,
            environment='production'
        )
        print("DevPulse initialized successfully")
    except Exception as e:
        print(f"DevPulse initialization warning: {e}")
    
    # Start both servers concurrently
    try:
        await asyncio.gather(
            start_websocket_server(),
            start_api_server(),
            return_exceptions=True
        )
    except Exception as e:
        print(f"Error in main: {e}")
        # Keep the container running even if there are errors
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())