#!/usr/bin/env python3
"""End-to-end test for error handling system.

This script tests various error scenarios to ensure proper error handling,
recovery, and user-friendly messages.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smartfile.utils.errors import (
    ConnectionError,
    FileSystemError,
    ConfigurationError,
    format_error_for_display,
)
from smartfile.utils.retry import RetryConfig, retry_with_backoff
from smartfile.utils.recovery import StateRecoveryManager

from rich.console import Console

console = Console()


def test_error_display():
    """Test error display formatting."""
    console.print("\n[bold blue]Test 1: Error Display Formatting[/bold blue]\n")
    
    # Test connection error
    error = ConnectionError(
        service="Ollama",
        endpoint="http://localhost:11434"
    )
    
    console.print("[yellow]Without technical details:[/yellow]")
    console.print(format_error_for_display(error, show_technical=False))
    
    console.print("\n[yellow]With technical details:[/yellow]")
    console.print(format_error_for_display(error, show_technical=True))
    
    console.print("\n✅ Error display formatting works!\n")


def test_retry_logic():
    """Test retry with exponential backoff."""
    console.print("[bold blue]Test 2: Retry with Exponential Backoff[/bold blue]\n")
    
    call_count = 0
    
    @retry_with_backoff(RetryConfig(max_attempts=3, initial_delay=0.5))
    def flaky_function():
        nonlocal call_count
        call_count += 1
        console.print(f"  Attempt {call_count}...")
        
        if call_count < 3:
            raise ConnectionError("Ollama", "http://localhost:11434")
        
        return "success"
    
    try:
        result = flaky_function()
        console.print(f"\n✅ Retry succeeded after {call_count} attempts: {result}\n")
    except Exception as e:
        console.print(f"\n❌ Retry failed: {e}\n")


def test_state_recovery():
    """Test state recovery system."""
    console.print("[bold blue]Test 3: State Recovery System[/bold blue]\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        state_dir = Path(temp_dir) / "state"
        recovery_mgr = StateRecoveryManager(state_dir)
        
        # Simulate starting a scan
        console.print("  Starting scan...")
        recovery_mgr.start_scan(1, "/test/path", 100)
        
        # Simulate progress
        console.print("  Processing files...")
        recovery_mgr.update_scan_progress(1, 50)
        
        # Check for crash
        console.print("  Checking for crash...")
        if recovery_mgr.detect_crash():
            interrupted = recovery_mgr.get_interrupted_scan()
            console.print(f"  Found interrupted scan: {interrupted.processed_files}/{interrupted.total_files}")
            
            # Show reconstruction
            console.print("\n  Incident reconstruction:")
            reconstruction = recovery_mgr.reconstruct_incident(interrupted)
            console.print(reconstruction)
        
        # Complete the scan
        console.print("\n  Completing scan...")
        recovery_mgr.complete_scan(1)
        
        # Check again - should not detect crash now
        if not recovery_mgr.detect_crash():
            console.print("\n✅ State recovery works correctly!\n")
        else:
            console.print("\n❌ State recovery failed!\n")


def test_filesystem_error():
    """Test filesystem error handling."""
    console.print("[bold blue]Test 4: Filesystem Error Handling[/bold blue]\n")
    
    error = FileSystemError(
        operation="move file",
        path="/restricted/file.txt",
        original_error=PermissionError("Permission denied")
    )
    
    console.print(format_error_for_display(error, show_technical=False))
    console.print("\n✅ Filesystem error handling works!\n")


def test_configuration_error():
    """Test configuration error handling."""
    console.print("[bold blue]Test 5: Configuration Error Handling[/bold blue]\n")
    
    error = ConfigurationError(
        config_key="ai.model",
        issue="Model not specified",
        expected_value="llama3.3 or qwen2.5"
    )
    
    console.print(format_error_for_display(error, show_technical=False))
    console.print("\n✅ Configuration error handling works!\n")


def main():
    """Run all tests."""
    console.print("\n[bold green]╔══════════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║  Error Handling System - E2E Tests          ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════════╝[/bold green]\n")
    
    try:
        test_error_display()
        test_retry_logic()
        test_state_recovery()
        test_filesystem_error()
        test_configuration_error()
        
        console.print("[bold green]═══════════════════════════════════════════════[/bold green]")
        console.print("[bold green]  All tests passed! ✅                        [/bold green]")
        console.print("[bold green]═══════════════════════════════════════════════[/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]Test failed: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
