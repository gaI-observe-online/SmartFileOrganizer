"""File categorization system."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.config import Config


class Categorizer:
    """Categorize files using 4-level system."""
    
    def __init__(self, config: Config):
        """Initialize categorizer.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.rules = config.get('rules', {})
    
    def categorize(
        self, 
        file_path: Path, 
        content: str = "", 
        metadata: Dict = None
    ) -> Tuple[str, str, str, str]:
        """Categorize file using 4-level system.
        
        Levels:
        1. Type: Documents, Images, Code, Finance, Videos, Audio, Archives
        2. Context: Work, Personal, Projects, Clients (AI-determined)
        3. Time: 2024, 2024-12, 2024-12-31
        4. Smart: AI-detected project/client/topic names
        
        Args:
            file_path: Path to file
            content: File content
            metadata: File metadata
            
        Returns:
            Tuple of (level1, level2, level3, level4)
        """
        metadata = metadata or {}
        
        # Level 1: Type-based categorization
        level1 = self._categorize_by_type(file_path, content)
        
        # Level 2: Context (default to "General" for now, AI will enhance)
        level2 = self._categorize_by_context(file_path, content, metadata)
        
        # Level 3: Time-based categorization
        level3 = self._categorize_by_time(file_path)
        
        # Level 4: Smart categorization (placeholder for AI enhancement)
        level4 = self._categorize_smart(file_path, content, metadata)
        
        return level1, level2, level3, level4
    
    def _categorize_by_type(self, file_path: Path, content: str = "") -> str:
        """Level 1: Categorize by file type.
        
        Args:
            file_path: Path to file
            content: File content
            
        Returns:
            Category name
        """
        suffix = file_path.suffix.lower()
        
        # Check finance first (more specific)
        finance_rule = self.rules.get('finance', {})
        if suffix in finance_rule.get('extensions', []):
            # Check for finance keywords in filename or content
            keywords = finance_rule.get('keywords', [])
            name_lower = file_path.name.lower()
            content_lower = content.lower()
            
            if any(kw in name_lower or kw in content_lower for kw in keywords):
                return "Finance"
        
        # Check other categories
        for category, rule in self.rules.items():
            if category == 'finance':
                continue
            
            extensions = rule.get('extensions', [])
            if suffix in extensions:
                return rule.get('folder', category.capitalize())
        
        # Default
        return "Other"
    
    def _categorize_by_context(
        self, 
        file_path: Path, 
        content: str = "", 
        metadata: Dict = None
    ) -> str:
        """Level 2: Categorize by context.
        
        This is a basic implementation. AI will enhance this.
        
        Args:
            file_path: Path to file
            content: File content
            metadata: File metadata
            
        Returns:
            Context category
        """
        # Check path for context clues
        path_str = str(file_path).lower()
        
        if any(word in path_str for word in ['work', 'office', 'business']):
            return "Work"
        elif any(word in path_str for word in ['personal', 'home', 'private']):
            return "Personal"
        elif any(word in path_str for word in ['project', 'dev', 'code']):
            return "Projects"
        elif any(word in path_str for word in ['client', 'customer']):
            return "Clients"
        
        # Check filename
        name_lower = file_path.name.lower()
        if any(word in name_lower for word in ['work', 'office', 'meeting', 'report']):
            return "Work"
        
        return "General"
    
    def _categorize_by_time(self, file_path: Path) -> str:
        """Level 3: Categorize by time.
        
        Args:
            file_path: Path to file
            
        Returns:
            Time category (e.g., "2024", "2024-12", or "2024-12-31")
        """
        # Use file modification time or creation time
        try:
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Check config preference for date folder format
                if self.config.get('preferences.create_date_folders', False):
                    # Full date: 2024-12-31
                    return mtime.strftime('%Y-%m-%d')
                else:
                    # Year only: 2024
                    return mtime.strftime('%Y')
        except (OSError, ValueError):
            pass
        
        return datetime.now().strftime('%Y')
    
    def _categorize_smart(
        self, 
        file_path: Path, 
        content: str = "", 
        metadata: Dict = None
    ) -> str:
        """Level 4: Smart categorization.
        
        This extracts project names, client names, or topics from content.
        Basic implementation - AI will enhance this.
        
        Args:
            file_path: Path to file
            content: File content
            metadata: File metadata
            
        Returns:
            Smart category
        """
        # Try to extract from filename
        name = file_path.stem
        
        # Remove common prefixes/suffixes
        for prefix in ['draft_', 'final_', 'copy_', 'new_']:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
        
        # Extract potential project/client name from filename
        # e.g., "ProjectX_report.pdf" → "ProjectX"
        parts = name.split('_')
        if len(parts) > 1:
            return parts[0].capitalize()
        
        parts = name.split('-')
        if len(parts) > 1:
            return parts[0].capitalize()
        
        return ""
    
    def build_path(
        self, 
        base_dir: Path, 
        level1: str, 
        level2: str = "", 
        level3: str = "", 
        level4: str = ""
    ) -> Path:
        """Build organized path from category levels.
        
        Args:
            base_dir: Base directory
            level1: Type category
            level2: Context category
            level3: Time category
            level4: Smart category
            
        Returns:
            Complete path
        """
        parts = [base_dir]
        
        if level1:
            parts.append(level1)
        
        if level2 and level2 != "General":
            parts.append(level2)
        
        if level3 and self.config.get('preferences.create_date_folders', False):
            parts.append(level3)
        
        if level4:
            parts.append(level4)
        
        return Path(*parts)
