"""File scanner for discovering files to organize."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import Config
from ..utils.errors import FileSystemError
from .extractor import ContentExtractor
from .categorizer import Categorizer
from .risk import RiskAssessor


logger = logging.getLogger(__name__)


class FileInfo:
    """Information about a scanned file."""
    
    def __init__(
        self,
        path: Path,
        size: int = 0,
        content: str = "",
        metadata: Dict = None,
        doc_type: str = "unknown",
        categories: tuple = ("", "", "", ""),
        risk_score: int = 0,
        risk_reasons: List[str] = None
    ):
        """Initialize file info.
        
        Args:
            path: File path
            size: File size in bytes
            content: Extracted content
            metadata: File metadata
            doc_type: Document type
            categories: 4-level categorization tuple
            risk_score: Risk score (0-100)
            risk_reasons: List of risk factors
        """
        self.path = path
        self.size = size
        self.content = content
        self.metadata = metadata or {}
        self.doc_type = doc_type
        self.categories = categories
        self.risk_score = risk_score
        self.risk_reasons = risk_reasons or []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "size": self.size,
            "content_preview": self.content[:200] if self.content else "",
            "metadata": self.metadata,
            "doc_type": self.doc_type,
            "categories": {
                "type": self.categories[0],
                "context": self.categories[1],
                "time": self.categories[2],
                "smart": self.categories[3]
            },
            "risk": {
                "score": self.risk_score,
                "level": self._get_risk_level(),
                "reasons": self.risk_reasons
            }
        }
    
    def _get_risk_level(self) -> str:
        """Get risk level from score."""
        if self.risk_score <= 30:
            return "low"
        elif self.risk_score <= 70:
            return "medium"
        else:
            return "high"


class Scanner:
    """Scan directory for files to organize."""
    
    def __init__(
        self,
        config: Config,
        extractor: ContentExtractor,
        categorizer: Categorizer,
        risk_assessor: RiskAssessor
    ):
        """Initialize scanner.
        
        Args:
            config: Configuration instance
            extractor: Content extractor
            categorizer: Categorizer
            risk_assessor: Risk assessor
        """
        self.config = config
        self.extractor = extractor
        self.categorizer = categorizer
        self.risk_assessor = risk_assessor
    
    def scan(self, directory: Path, recursive: bool = False) -> List[FileInfo]:
        """Scan directory for files.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively
            
        Returns:
            List of FileInfo objects
        """
        files = []
        
        if not directory.exists():
            raise FileSystemError(
                operation="scan directory",
                path=str(directory),
                original_error=FileNotFoundError(f"Directory not found: {directory}")
            )
        
        if not directory.is_dir():
            raise FileSystemError(
                operation="scan directory",
                path=str(directory),
                original_error=ValueError(f"Path is not a directory: {directory}")
            )
        
        # Get ignore_hidden setting
        ignore_hidden = self.config.get('preferences.ignore_hidden', True)
        
        # Scan directory
        pattern = "**/*" if recursive else "*"
        
        try:
            for path in directory.glob(pattern):
                # Skip directories
                if path.is_dir():
                    continue
                
                # Skip hidden files if configured
                if ignore_hidden and path.name.startswith('.'):
                    continue
                
                # Skip files in .organizer directory
                if '.organizer' in path.parts:
                    continue
                
                try:
                    file_info = self._analyze_file(path)
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"Error analyzing file {path}: {e}")
                    continue
        
        except PermissionError as e:
            raise FileSystemError(
                operation="scan directory",
                path=str(directory),
                original_error=e
            )
        
        logger.info(f"Scanned {directory}: found {len(files)} files")
        return files
    
    def _analyze_file(self, path: Path) -> FileInfo:
        """Analyze a single file.
        
        Args:
            path: File path
            
        Returns:
            FileInfo object
        """
        # Get file size
        size = path.stat().st_size
        
        # Extract content (skip very large files for content extraction)
        extracted = {"content": "", "metadata": {}, "doc_type": "unknown"}
        if size < 100 * 1024 * 1024:  # < 100MB
            extracted = self.extractor.extract(path)
        
        content = extracted.get("content", "")
        metadata = extracted.get("metadata", {})
        doc_type = extracted.get("doc_type", "unknown")
        
        # Categorize
        categories = self.categorizer.categorize(path, content, metadata)
        
        # Assess risk
        risk_score, risk_reasons = self.risk_assessor.calculate_risk_score(
            path, content, size
        )
        
        return FileInfo(
            path=path,
            size=size,
            content=content,
            metadata=metadata,
            doc_type=doc_type,
            categories=categories,
            risk_score=risk_score,
            risk_reasons=risk_reasons
        )
    
    def get_file_statistics(self, files: List[FileInfo]) -> Dict:
        """Get statistics about scanned files.
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total": len(files),
            "by_type": {},
            "by_risk": {"low": 0, "medium": 0, "high": 0},
            "total_size": 0
        }
        
        for file in files:
            # Count by type
            file_type = file.categories[0]
            stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1
            
            # Count by risk
            risk_level = file._get_risk_level()
            stats["by_risk"][risk_level] += 1
            
            # Total size
            stats["total_size"] += file.size
        
        return stats
