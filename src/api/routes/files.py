"""File and category endpoints."""

from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class FileInfo(BaseModel):
    """File information model."""
    path: str
    name: str
    size: int
    category: str
    risk_score: int
    risk_level: str
    confidence: float


class CategoryStats(BaseModel):
    """Category statistics model."""
    category: str
    count: int
    total_size: int


@router.get("/files", response_model=List[FileInfo])
async def list_files(
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0
):
    """List scanned files with optional filtering.
    
    Args:
        category: Filter by category (optional)
        risk_level: Filter by risk level (low/medium/high)
        limit: Maximum number of files to return
        offset: Offset for pagination
        
    Returns:
        List of files matching filters
    """
    from ...smartfile.core.config import Config
    from ...smartfile.core.database import Database
    
    config = Config()
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    
    # Query files from database
    # This is a simplified version - you would need to add appropriate queries to Database class
    cursor = db.conn.cursor()
    
    query = "SELECT * FROM moves ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params = [limit, offset]
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    files = []
    for row in rows:
        # Simplified - adjust based on actual database schema
        files.append(FileInfo(
            path=row[1] if len(row) > 1 else "",
            name=Path(row[1]).name if len(row) > 1 else "",
            size=0,  # Would need to be stored in DB
            category="unknown",  # Would need to be stored in DB
            risk_score=0,
            risk_level="low",
            confidence=0.8
        ))
    
    db.close()
    
    return files


@router.get("/categories", response_model=List[CategoryStats])
async def get_categories():
    """Get file category statistics.
    
    Returns:
        Statistics for each category
    """
    from ...smartfile.core.config import Config
    
    config = Config()
    
    # Get categories from config
    rules = config.get('rules', {})
    
    # This is a simplified version - in production, query actual file counts from database
    stats = []
    for category_name, category_config in rules.items():
        stats.append(CategoryStats(
            category=category_name,
            count=0,  # Would query from database
            total_size=0  # Would query from database
        ))
    
    return stats
