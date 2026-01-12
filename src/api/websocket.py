"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, scan_id: str):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = set()
        
        self.active_connections[scan_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, scan_id: str):
        """Remove a WebSocket connection."""
        if scan_id in self.active_connections:
            self.active_connections[scan_id].discard(websocket)
            
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]
    
    async def broadcast(self, scan_id: str, message: dict):
        """Broadcast a message to all connections for a scan."""
        if scan_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[scan_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, scan_id)


manager = ConnectionManager()


@router.websocket("/ws/scan/{scan_id}")
async def websocket_scan_updates(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint for real-time scan progress updates.
    
    Args:
        websocket: WebSocket connection
        scan_id: Scan identifier to subscribe to
    """
    from .routes.scan import active_scans
    
    await manager.connect(websocket, scan_id)
    
    try:
        # Send initial status
        if scan_id in active_scans:
            await websocket.send_json({
                "type": "progress",
                "data": active_scans[scan_id]
            })
        
        # Keep connection alive and send updates
        while True:
            # Check for updates every second
            await asyncio.sleep(1)
            
            if scan_id in active_scans:
                scan = active_scans[scan_id]
                
                # Send progress update
                await websocket.send_json({
                    "type": "progress",
                    "data": {
                        "status": scan["status"],
                        "total_files": scan["total_files"],
                        "processed_files": scan["processed_files"],
                        "current_file": scan.get("current_file"),
                        "progress_percent": scan["progress_percent"],
                    }
                })
                
                # If scan is completed or cancelled, close connection
                if scan["status"] in ["completed", "cancelled", "error"]:
                    await websocket.send_json({
                        "type": "complete",
                        "data": {"status": scan["status"]}
                    })
                    break
            else:
                # Scan not found
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Scan not found"}
                })
                break
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, scan_id)
    except Exception as e:
        manager.disconnect(websocket, scan_id)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        except Exception:
            pass
