"""Database management for audit trail."""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.errors import DatabaseError


logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for audit trail."""
    
    def __init__(self, db_path: Path):
        """Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database schema."""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Scans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    path TEXT NOT NULL,
                    file_count INTEGER NOT NULL
                )
            """)
            
            # Proposals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_approved BOOLEAN,
                    rolled_back BOOLEAN DEFAULT 0,
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)
            
            # Moves table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id INTEGER NOT NULL,
                    original_path TEXT NOT NULL,
                    new_path TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id)
                )
            """)
            
            # Learning data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_type TEXT NOT NULL,
                    target_folder TEXT NOT NULL,
                    user_approved BOOLEAN NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            self.conn.commit()
        
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(
                operation="initialize database",
                original_error=e
            )
    
    def add_scan(self, path: str, file_count: int) -> int:
        """Add scan record.
        
        Args:
            path: Scanned path
            file_count: Number of files found
            
        Returns:
            Scan ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO scans (timestamp, path, file_count) VALUES (?, ?, ?)",
            (datetime.now(), path, file_count)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def add_proposal(self, scan_id: int, plan: str, confidence: float) -> int:
        """Add proposal record.
        
        Args:
            scan_id: Associated scan ID
            plan: Organization plan (JSON string)
            confidence: AI confidence score
            
        Returns:
            Proposal ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO proposals (scan_id, plan, confidence, timestamp) VALUES (?, ?, ?, ?)",
            (scan_id, plan, confidence, datetime.now())
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_proposal_approval(self, proposal_id: int, approved: bool) -> None:
        """Update proposal approval status.
        
        Args:
            proposal_id: Proposal ID
            approved: Whether user approved
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE proposals SET user_approved = ? WHERE id = ?",
            (approved, proposal_id)
        )
        self.conn.commit()
    
    def add_move(self, proposal_id: int, original_path: str, new_path: str) -> int:
        """Add move record.
        
        Args:
            proposal_id: Associated proposal ID
            original_path: Original file path
            new_path: New file path
            
        Returns:
            Move ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO moves (proposal_id, original_path, new_path, timestamp) VALUES (?, ?, ?, ?)",
            (proposal_id, original_path, new_path, datetime.now())
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def add_learning_data(self, file_type: str, target_folder: str, approved: bool) -> int:
        """Add learning data record.
        
        Args:
            file_type: File type/pattern
            target_folder: Target folder
            approved: Whether user approved
            
        Returns:
            Learning data ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO learning_data (file_type, target_folder, user_approved, timestamp) VALUES (?, ?, ?, ?)",
            (file_type, target_folder, approved, datetime.now())
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_recent_scans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent scans.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of scan records
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get proposal by ID.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal record or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_moves_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get moves for a proposal.
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            List of move records
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM moves WHERE proposal_id = ? ORDER BY timestamp",
            (proposal_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_proposal_rolled_back(self, proposal_id: int) -> None:
        """Mark proposal as rolled back.
        
        Args:
            proposal_id: Proposal ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE proposals SET rolled_back = 1 WHERE id = ?",
            (proposal_id,)
        )
        self.conn.commit()
    
    def get_learning_patterns(self, file_type: str, min_count: int = 10) -> List[Tuple[str, int, float]]:
        """Get learned patterns for a file type.
        
        Args:
            file_type: File type to query
            min_count: Minimum number of occurrences
            
        Returns:
            List of (target_folder, count, approval_rate) tuples
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                target_folder,
                COUNT(*) as count,
                SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as approval_rate
            FROM learning_data
            WHERE file_type = ?
            GROUP BY target_folder
            HAVING count >= ?
            ORDER BY count DESC, approval_rate DESC
        """, (file_type, min_count))
        return cursor.fetchall()
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
