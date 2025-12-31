"""Risk assessment engine for file operations."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

from ..utils.redaction import SensitiveDataRedactor


class RiskAssessor:
    """Assess risk level for file operations."""
    
    # Risk thresholds
    LOW_RISK_MAX = 30
    MEDIUM_RISK_MAX = 70
    HIGH_RISK_MIN = 71
    
    # System file extensions
    SYSTEM_EXTENSIONS = {'.dll', '.sys', '.exe', '.so', '.dylib'}
    
    def __init__(self, redactor: SensitiveDataRedactor):
        """Initialize risk assessor.
        
        Args:
            redactor: Sensitive data redactor instance
        """
        self.redactor = redactor
    
    def calculate_risk_score(
        self, 
        file_path: Path, 
        content: str = "", 
        file_size: int = 0
    ) -> Tuple[int, List[str]]:
        """Calculate risk score for a file.
        
        Risk Scoring:
        - SSN/Credit card patterns: +40
        - Passwords/API keys: +50
        - Large files >500MB: +10
        - System files (.dll, .sys): +30
        - Recently modified (<24h): +20
        
        Args:
            file_path: Path to file
            content: File content (optional)
            file_size: File size in bytes
            
        Returns:
            Tuple of (risk_score, reasons)
        """
        score = 0
        reasons = []
        
        # Check for sensitive content patterns
        if content:
            sensitive = self.redactor.detect_sensitive_content(content)
            
            for pattern_type, description in sensitive:
                if pattern_type in ["SSN", "CreditCard"]:
                    score += 40
                    reasons.append(f"{description} (+40)")
                elif pattern_type in ["Password", "APIKey"]:
                    score += 50
                    reasons.append(f"{description} (+50)")
                elif pattern_type in ["Email", "Phone"]:
                    score += 10
                    reasons.append(f"{description} (+10)")
        
        # Large file check (>500MB)
        if file_size > 500 * 1024 * 1024:
            score += 10
            reasons.append(f"Large file (>500MB) (+10)")
        
        # System file check
        if file_path.suffix.lower() in self.SYSTEM_EXTENSIONS:
            score += 30
            reasons.append(f"System file extension ({file_path.suffix}) (+30)")
        
        # Recently modified check (<24h)
        if file_path.exists():
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if datetime.now() - mtime < timedelta(hours=24):
                    score += 20
                    reasons.append("Recently modified (<24h) (+20)")
            except (OSError, ValueError):
                pass
        
        return min(score, 100), reasons
    
    def get_risk_level(self, score: int) -> str:
        """Get risk level from score.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk level: "low", "medium", or "high"
        """
        if score <= self.LOW_RISK_MAX:
            return "low"
        elif score <= self.MEDIUM_RISK_MAX:
            return "medium"
        else:
            return "high"
    
    def requires_approval(self, score: int, auto_approve_threshold: int) -> bool:
        """Check if operation requires user approval.
        
        Args:
            score: Risk score
            auto_approve_threshold: Auto-approve threshold from config
            
        Returns:
            True if approval required
        """
        return score > auto_approve_threshold
    
    def get_risk_color(self, score: int) -> str:
        """Get color for risk display (for rich library).
        
        Args:
            score: Risk score
            
        Returns:
            Color name
        """
        level = self.get_risk_level(score)
        return {
            "low": "green",
            "medium": "yellow",
            "high": "red"
        }[level]
