"""Standalone DevPulse API server with fixed database access."""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("devpulse_api")

# Create FastAPI app
app = FastAPI(title="DevPulse API", description="DevPulse API with fixed database access")


def get_recent_trace_ids_direct(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent trace IDs using direct SQLite connection."""
    
    # Get database file path from environment
    db_url = os.getenv('DEVPULSE_DB_URL', 'sqlite:///app/data/devpulse.db')
    
    if not db_url.startswith("sqlite:///"):
        logger.error("Direct access only supports SQLite databases")
        return []
    
    db_file = db_url.replace("sqlite:///", "")
    
    # For container environment, use the mounted path
    if not os.path.exists(db_file):
        # Try alternative paths
        alt_paths = [
            "/app/data/devpulse.db",
            "./data/devpulse.db",
            "../data/devpulse.db"
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                db_file = alt_path
                break
        else:
            logger.error(f"Database file not found: {db_file}")
            return []
    
    try:
        # Use direct SQLite connection
        conn = sqlite3.connect(db_file, timeout=30.0)
        
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL;")
        
        cursor = conn.cursor()
        
        # Query to get recent trace IDs with their latest event information
        query = """
        SELECT 
            e1.trace_id,
            e1.system,
            e1.event_type,
            e1.payload,
            e1.timestamp,
            COUNT(e2.id) as event_count
        FROM events e1
        INNER JOIN (
            SELECT trace_id, MAX(timestamp) as latest_timestamp
            FROM events
            GROUP BY trace_id
        ) latest ON e1.trace_id = latest.trace_id AND e1.timestamp = latest.latest_timestamp
        LEFT JOIN events e2 ON e1.trace_id = e2.trace_id
        GROUP BY e1.trace_id, e1.system, e1.event_type, e1.payload, e1.timestamp
        ORDER BY e1.timestamp DESC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            trace_id, system, event_type, payload, timestamp, event_count = row
            
            try:
                # Parse the payload JSON
                payload_data = json.loads(payload) if payload else {}
                
                result.append({
                    'trace_id': trace_id,
                    'latest_timestamp': timestamp,
                    'system': system,
                    'event_type': event_type,
                    'event_count': event_count,
                    'latest_event': payload_data
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode event payload for trace {trace_id}")
                result.append({
                    'trace_id': trace_id,
                    'latest_timestamp': timestamp,
                    'system': system,
                    'event_type': event_type,
                    'event_count': event_count,
                    'latest_event': {}
                })
        
        conn.close()
        logger.info(f"Successfully retrieved {len(result)} traces from database")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get recent trace IDs from database: {str(e)}")
        return []


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    
    db_url = os.getenv('DEVPULSE_DB_URL', 'sqlite:///app/data/devpulse.db')
    db_file = db_url.replace("sqlite:///", "")
    
    # For container environment, use the mounted path
    if not os.path.exists(db_file):
        alt_paths = [
            "/app/data/devpulse.db",
            "./data/devpulse.db",
            "../data/devpulse.db"
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                db_file = alt_path
                break
        else:
            return {"error": f"Database file not found: {db_file}"}
    
    try:
        conn = sqlite3.connect(db_file, timeout=30.0)
        cursor = conn.cursor()
        
        # Get total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        # Get total traces
        cursor.execute("SELECT COUNT(DISTINCT trace_id) FROM events")
        total_traces = cursor.fetchone()[0]
        
        # Get latest event timestamp
        cursor.execute("SELECT MAX(timestamp) FROM events")
        latest_timestamp = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_events": total_events,
            "total_traces": total_traces,
            "latest_timestamp": latest_timestamp,
            "database_file": db_file
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "DevPulse API Server",
        "version": "1.0.0",
        "endpoints": [
            "/api/traces",
            "/api/stats",
            "/health"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = get_database_stats()
    if "error" in stats:
        raise HTTPException(status_code=500, detail=f"Database error: {stats['error']}")
    
    return {
        "status": "healthy",
        "database": "connected",
        "stats": stats
    }


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    stats = get_database_stats()
    if "error" in stats:
        raise HTTPException(status_code=500, detail=f"Database error: {stats['error']}")
    
    return stats


@app.get("/api/traces")
async def get_traces(limit: int = 20):
    """API endpoint to get recent traces."""
    
    if limit > 100:
        limit = 100  # Cap the limit
    
    try:
        traces = get_recent_trace_ids_direct(limit)
        
        return {
            "traces": traces,
            "count": len(traces),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting traces: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get traces: {str(e)}")


@app.get("/ui", response_class=HTMLResponse)
async def web_ui():
    """Simple web UI for viewing traces."""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevPulse - Trace Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .trace-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
            .trace-id { font-weight: bold; color: #007bff; }
            .trace-meta { color: #666; font-size: 0.9em; margin-top: 5px; }
            .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DevPulse - Trace Viewer</h1>
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
            
            <div class="stats" id="stats">Loading stats...</div>
            
            <div id="traces">Loading traces...</div>
        </div>
        
        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    document.getElementById('stats').innerHTML = `
                        <h3>Database Statistics</h3>
                        <p>Total Events: ${stats.total_events}</p>
                        <p>Total Traces: ${stats.total_traces}</p>
                        <p>Latest Event: ${stats.latest_timestamp}</p>
                        <p>Database File: ${stats.database_file}</p>
                    `;
                } catch (error) {
                    document.getElementById('stats').innerHTML = `<p style="color: red;">Error loading stats: ${error}</p>`;
                }
            }
            
            async function loadTraces() {
                try {
                    const response = await fetch('/api/traces?limit=20');
                    const data = await response.json();
                    
                    if (data.traces.length === 0) {
                        document.getElementById('traces').innerHTML = '<p>No traces found.</p>';
                        return;
                    }
                    
                    let html = `<h3>Recent Traces (${data.count})</h3>`;
                    data.traces.forEach(trace => {
                        html += `
                            <div class="trace-item">
                                <div class="trace-id">${trace.trace_id}</div>
                                <div class="trace-meta">
                                    System: ${trace.system} | 
                                    Event: ${trace.event_type} | 
                                    Count: ${trace.event_count} | 
                                    Last: ${trace.latest_timestamp}
                                </div>
                            </div>
                        `;
                    });
                    document.getElementById('traces').innerHTML = html;
                } catch (error) {
                    document.getElementById('traces').innerHTML = `<p style="color: red;">Error loading traces: ${error}</p>`;
                }
            }
            
            // Load data on page load
            loadStats();
            loadTraces();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    # Set environment variable if not set
    if not os.getenv('DEVPULSE_DB_URL'):
        os.environ['DEVPULSE_DB_URL'] = 'sqlite:///app/data/devpulse.db'
    
    print("Starting DevPulse API Server...")
    print(f"Database URL: {os.getenv('DEVPULSE_DB_URL')}")
    
    uvicorn.run(app, host="0.0.0.0", port=8089)