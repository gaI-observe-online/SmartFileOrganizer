"""Main CLI interface for SmartFileOrganizer."""

import os
import sys
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from ..core.config import Config
from ..core.database import Database
from ..audit.trail import AuditTrail
from ..analysis.scanner import Scanner
from ..analysis.extractor import ContentExtractor
from ..analysis.categorizer import Categorizer
from ..analysis.risk import RiskAssessor
from ..utils.redaction import SensitiveDataRedactor
from ..ai.ollama_provider import OllamaProvider
from ..core.organizer import Organizer
from ..core.rollback import RollbackManager


console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="SmartFileOrganizer")
@click.option('--config', type=click.Path(), help='Path to config file')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """SmartFileOrganizer - AI-powered intelligent file organization."""
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize configuration
    config_path = Path(config) if config else None
    ctx.obj = {'config': Config(config_path)}
    
    # Ensure .organizer directory exists
    ctx.obj['config'].ensure_organizer_dir()


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview changes without executing')
@click.option('--batch', is_flag=True, help='Batch mode with minimal interaction')
@click.option('--auto-approve-threshold', type=int, help='Auto-approve threshold (0-100)')
@click.option('--recursive', is_flag=True, help='Scan recursively')
@click.pass_context
def scan(ctx, path, dry_run, batch, auto_approve_threshold, recursive):
    """Scan and organize files in a directory."""
    config = ctx.obj['config']
    
    # Override config if specified
    if auto_approve_threshold is not None:
        config.set('preferences.auto_approve_threshold', auto_approve_threshold)
    
    if dry_run:
        config.set('preferences.dry_run', True)
    
    # Initialize components
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    audit = AuditTrail(organizer_dir, db)
    redactor = SensitiveDataRedactor(config.get('privacy.redact_sensitive_in_logs', True))
    
    # Initialize analysis components
    extractor = ContentExtractor()
    categorizer = Categorizer(config)
    risk_assessor = RiskAssessor(redactor)
    scanner = Scanner(config, extractor, categorizer, risk_assessor)
    
    # Initialize AI provider
    ai_config = config.get('ai.models.ollama', {})
    ai_provider = OllamaProvider(
        endpoint=ai_config.get('endpoint', 'http://localhost:11434'),
        model=ai_config.get('model', 'llama3.3'),
        fallback_model=ai_config.get('fallback_model', 'qwen2.5'),
        timeout=ai_config.get('timeout', 30)
    )
    
    # Initialize organizer
    organizer = Organizer(config, db, audit, scanner, categorizer, ai_provider)
    
    # Scan directory
    console.print(Panel(f"[bold blue]Scanning:[/bold blue] {path}", expand=False))
    
    scan_id, files = organizer.scan_directory(Path(path), recursive)
    
    if not files:
        console.print("[yellow]No files found to organize.[/yellow]")
        return
    
    # Display scan results
    stats = scanner.get_file_statistics(files)
    _display_scan_results(stats)
    
    # Generate proposal
    console.print("\n[bold blue]Generating organization proposal...[/bold blue]")
    
    base_dir = Path(path).parent / "Organized"
    proposal = organizer.generate_proposal(scan_id, files, base_dir)
    
    # Display proposal
    _display_proposal(proposal, config.get('preferences.auto_approve_threshold', 30))
    
    # Get user approval (unless batch mode with auto-approve)
    if batch:
        # Auto-approve low-risk files
        threshold = config.get('preferences.auto_approve_threshold', 30)
        low_risk_files = [
            (f, d) for f, d in proposal.files if f.risk_score <= threshold
        ]
        
        if low_risk_files:
            console.print(f"\n[green]Auto-approving {len(low_risk_files)} low-risk files...[/green]")
            # Create a new proposal with only low-risk files
            from ..core.organizer import OrganizationProposal
            auto_proposal = OrganizationProposal(
                files=low_risk_files,
                confidence=proposal.confidence,
                reasoning=proposal.reasoning
            )
            auto_proposal.proposal_id = proposal.proposal_id
            
            success, moved = organizer.execute_proposal(auto_proposal, dry_run)
            
            if success:
                console.print(f"[green]✓ Successfully moved {moved} files[/green]")
            else:
                console.print(f"[red]✗ Error during execution[/red]")
        
        # Queue medium/high risk for review
        high_risk_files = [
            (f, d) for f, d in proposal.files if f.risk_score > threshold
        ]
        if high_risk_files:
            console.print(f"[yellow]⚠ {len(high_risk_files)} files queued for manual review[/yellow]")
    
    else:
        # Interactive mode
        if click.confirm('\nProceed with organization?', default=False):
            audit.log_approval(proposal.proposal_id, True)
            
            success, moved = organizer.execute_proposal(proposal, dry_run)
            
            if success:
                console.print(f"\n[green]✓ Successfully moved {moved} files[/green]")
                if dry_run:
                    console.print("[yellow](Dry run - no actual changes made)[/yellow]")
            else:
                console.print(f"\n[red]✗ Error during execution[/red]")
        else:
            audit.log_approval(proposal.proposal_id, False)
            console.print("[yellow]Organization cancelled[/yellow]")
    
    db.close()


def _display_scan_results(stats: dict):
    """Display scan results."""
    console.print(Panel.fit(
        f"[bold]Total Files:[/bold] {stats['total']}\n"
        f"[bold]Total Size:[/bold] {_format_size(stats['total_size'])}\n\n"
        f"[bold]By Type:[/bold]\n" +
        "\n".join([f"  {k}: {v}" for k, v in stats['by_type'].items()]) +
        f"\n\n[bold]By Risk:[/bold]\n"
        f"  [green]Low:[/green] {stats['by_risk']['low']}\n"
        f"  [yellow]Medium:[/yellow] {stats['by_risk']['medium']}\n"
        f"  [red]High:[/red] {stats['by_risk']['high']}",
        title="📁 Scan Results",
        border_style="blue"
    ))


def _display_proposal(proposal, threshold: int):
    """Display organization proposal."""
    table = Table(title="Organization Proposal")
    
    table.add_column("File", style="cyan")
    table.add_column("Destination", style="green")
    table.add_column("Risk", justify="right")
    table.add_column("Conf", justify="right")
    
    for file_info, dest_path in proposal.files[:20]:  # Show first 20
        risk_level = file_info._get_risk_level()
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}[risk_level]
        
        table.add_row(
            file_info.path.name,
            str(dest_path.relative_to(dest_path.parents[1])),
            f"[{risk_color}]{file_info.risk_score}[/{risk_color}]",
            f"{proposal.confidence:.0%}"
        )
    
    if len(proposal.files) > 20:
        table.add_row("...", f"... and {len(proposal.files) - 20} more files", "", "")
    
    console.print(table)
    
    # Show auto-approve summary
    auto_approve = sum(1 for f, _ in proposal.files if f.risk_score <= threshold)
    review_required = len(proposal.files) - auto_approve
    
    console.print(f"\n[green]✅ Auto-approve:[/green] {auto_approve} files (low risk)")
    if review_required > 0:
        console.print(f"[yellow]⚠️  Review required:[/yellow] {review_required} files (medium/high risk)")


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


@cli.command()
@click.option('--last', is_flag=True, help='Rollback last operation')
@click.option('--proposal', type=int, help='Rollback specific proposal ID')
@click.option('--show-history', is_flag=True, help='Show rollback history')
@click.pass_context
def rollback(ctx, last, proposal, show_history):
    """Rollback file operations."""
    config = ctx.obj['config']
    
    # Initialize components
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    audit = AuditTrail(organizer_dir, db)
    rollback_mgr = RollbackManager(config, db, audit)
    
    if show_history:
        history = rollback_mgr.get_rollback_history()
        
        table = Table(title="Rollback History")
        table.add_column("Proposal ID", justify="right")
        table.add_column("Timestamp")
        table.add_column("Files", justify="right")
        table.add_column("Status")
        
        for record in history:
            status = "[red]Rolled Back[/red]" if record['rolled_back'] else "[green]Active[/green]"
            table.add_row(
                str(record['id']),
                str(record['timestamp']),
                str(record['file_count']),
                status
            )
        
        console.print(table)
    
    elif last:
        if click.confirm('Rollback last operation?', default=False):
            success, restored = rollback_mgr.rollback_last()
            
            if success:
                console.print(f"[green]✓ Restored {restored} files[/green]")
            else:
                console.print("[red]✗ Rollback failed[/red]")
    
    elif proposal:
        if click.confirm(f'Rollback proposal {proposal}?', default=False):
            success, restored = rollback_mgr.rollback_proposal(proposal)
            
            if success:
                console.print(f"[green]✓ Restored {restored} files[/green]")
            else:
                console.print("[red]✗ Rollback failed[/red]")
    
    else:
        console.print("[yellow]Please specify --last, --proposal, or --show-history[/yellow]")
    
    db.close()


@cli.command()
@click.option('--show', is_flag=True, help='Show current AI provider')
@click.option('--set-provider', type=click.Choice(['ollama', 'openai', 'anthropic']), help='Set AI provider')
@click.option('--model', type=str, help='Set model name')
@click.option('--api-key', type=str, help='Set API key (for OpenAI/Anthropic)')
@click.option('--edit', is_flag=True, help='Edit config file')
@click.pass_context
def config(ctx, show, set_provider, model, api_key, edit):
    """Manage configuration."""
    cfg = ctx.obj['config']
    
    if show:
        current = cfg.get('ai.primary', 'ollama')
        console.print(f"[bold]Current AI Provider:[/bold] {current}")
        
        if current == 'ollama':
            endpoint = cfg.get('ai.models.ollama.endpoint', 'http://localhost:11434')
            model_name = cfg.get('ai.models.ollama.model', 'llama3.3')
            console.print(f"[bold]Endpoint:[/bold] {endpoint}")
            console.print(f"[bold]Model:[/bold] {model_name}")
    
    elif set_provider:
        cfg.set('ai.primary', set_provider)
        
        if model:
            cfg.set(f'ai.models.{set_provider}.model', model)
        
        if api_key:
            cfg.set(f'ai.models.{set_provider}.api_key', api_key)
            cfg.set(f'ai.models.{set_provider}.enabled', True)
        
        console.print(f"[green]✓ AI provider set to {set_provider}[/green]")
    
    elif edit:
        import subprocess
        editor = os.getenv('EDITOR', 'nano')
        subprocess.call([editor, str(cfg.config_path)])
    
    else:
        console.print("[yellow]Use --show, --set-provider, or --edit[/yellow]")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--immediate', is_flag=True, help='Process files immediately')
@click.option('--queue-for-review', is_flag=True, help='Queue files for manual review')
@click.pass_context
def watch(ctx, path, immediate, queue_for_review):
    """Watch folder for new files and organize them automatically."""
    from .watch import WatchManager
    
    config = ctx.obj['config']
    
    # Initialize components
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    audit = AuditTrail(organizer_dir, db)
    redactor = SensitiveDataRedactor(config.get('privacy.redact_sensitive_in_logs', True))
    
    extractor = ContentExtractor()
    categorizer = Categorizer(config)
    risk_assessor = RiskAssessor(redactor)
    scanner = Scanner(config, extractor, categorizer, risk_assessor)
    
    ai_config = config.get('ai.models.ollama', {})
    ai_provider = OllamaProvider(
        endpoint=ai_config.get('endpoint', 'http://localhost:11434'),
        model=ai_config.get('model', 'llama3.3'),
        fallback_model=ai_config.get('fallback_model', 'qwen2.5'),
        timeout=ai_config.get('timeout', 30)
    )
    
    organizer = Organizer(config, db, audit, scanner, categorizer, ai_provider)
    
    # Determine mode
    if immediate:
        mode = "immediate"
    elif queue_for_review:
        mode = "queue"
    else:
        mode = "batch"
    
    console.print(f"[bold blue]👁 Watching:[/bold blue] {path}")
    console.print(f"[bold]Mode:[/bold] {mode}")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
    
    # Start watching
    watch_mgr = WatchManager(config, organizer)
    watch_mgr.watch(Path(path), mode)


@cli.command()
@click.option('--last', type=int, default=100, help='Show last N operations')
@click.option('--date', type=str, help='Filter by date (YYYY-MM-DD)')
@click.option('--file', type=str, help='Filter by filename')
@click.pass_context
def audit(ctx, last, date, file):
    """Show audit trail."""
    config = ctx.obj['config']
    
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    
    # Get recent scans
    scans = db.get_recent_scans(last)
    
    table = Table(title="Audit Trail")
    table.add_column("ID", justify="right")
    table.add_column("Timestamp")
    table.add_column("Path")
    table.add_column("Files", justify="right")
    
    for scan in scans:
        # Filter if needed
        if date and not scan['timestamp'].startswith(date):
            continue
        
        table.add_row(
            str(scan['id']),
            str(scan['timestamp']),
            scan['path'],
            str(scan['file_count'])
        )
    
    console.print(table)
    db.close()


@cli.command()
@click.option('--summary', is_flag=True, help='Show summary statistics')
@click.pass_context
def stats(ctx, summary):
    """Show statistics."""
    config = ctx.obj['config']
    
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    
    cursor = db.conn.cursor()
    
    # Get total scans
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]
    
    # Get total proposals
    cursor.execute("SELECT COUNT(*) FROM proposals")
    total_proposals = cursor.fetchone()[0]
    
    # Get total moves
    cursor.execute("SELECT COUNT(*) FROM moves")
    total_moves = cursor.fetchone()[0]
    
    # Get approved proposals
    cursor.execute("SELECT COUNT(*) FROM proposals WHERE user_approved = 1")
    approved = cursor.fetchone()[0]
    
    # Get rolled back proposals
    cursor.execute("SELECT COUNT(*) FROM proposals WHERE rolled_back = 1")
    rolled_back = cursor.fetchone()[0]
    
    console.print(Panel.fit(
        f"[bold]Total Scans:[/bold] {total_scans}\n"
        f"[bold]Total Proposals:[/bold] {total_proposals}\n"
        f"[bold]Approved:[/bold] {approved}\n"
        f"[bold]Rolled Back:[/bold] {rolled_back}\n"
        f"[bold]Total Files Moved:[/bold] {total_moves}",
        title="📊 Statistics",
        border_style="blue"
    ))
    
    db.close()


@cli.command()
@click.option('--port', type=int, help='Port to run web server on (default: 8001)')
@click.option('--host', type=str, default='127.0.0.1', help='Host to bind to')
@click.option('--no-browser', is_flag=True, help='Do not open browser automatically')
@click.pass_context
def serve(ctx, port, host, no_browser):
    """Start the web UI server."""
    import os
    import socket
    import webbrowser
    
    # Determine port (priority: CLI flag > env var > config > default)
    if port is None:
        port = int(os.getenv('SMARTFILE_PORT', '8001'))
        config = ctx.obj['config']
        port = config.get('web.port', port)
    
    # Check if port is available
    def is_port_available(port):
        """Check if a port is available."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            sock.close()
            return True
        except OSError:
            return False
    
    # Handle port conflicts
    if not is_port_available(port):
        console.print(f"[red]❌ Error: Port {port} is already in use[/red]\n")
        console.print("[bold]💡 Suggested actions:[/bold]")
        
        # Try to find alternative ports
        suggested_ports = []
        for alt_port in range(port + 1, port + 10):
            if is_port_available(alt_port):
                suggested_ports.append(alt_port)
                if len(suggested_ports) >= 3:
                    break
        
        if suggested_ports:
            console.print(f"  • Try port {suggested_ports[0]}: smartfile serve --port {suggested_ports[0]}")
            console.print(f"  • Stop the service using port {port}")
            console.print(f"  • Configure a custom port in settings")
            console.print(f"\n[green]🔍 Detecting available ports... Found: {', '.join(map(str, suggested_ports))}[/green]")
            
            # Ask if user wants to use alternative port
            if suggested_ports and click.confirm(f'\nUse port {suggested_ports[0]} instead?', default=True):
                port = suggested_ports[0]
            else:
                return
        else:
            console.print(f"  • Stop the service using port {port}")
            console.print(f"  • Configure a custom port with --port flag")
            return
    
    # Set environment variable for the server
    os.environ['SMARTFILE_PORT'] = str(port)
    
    console.print(Panel.fit(
        f"[bold green]🚀 Starting SmartFileOrganizer Web UI[/bold green]\n\n"
        f"[bold]URL:[/bold] http://{host}:{port}\n"
        f"[bold]Host:[/bold] {host}\n"
        f"[bold]Port:[/bold] {port}\n\n"
        f"[yellow]Press Ctrl+C to stop the server[/yellow]",
        title="SmartFileOrganizer Web Server",
        border_style="green"
    ))
    
    # Open browser
    if not no_browser:
        url = f"http://{host}:{port}"
        console.print(f"\n[blue]Opening browser at {url}...[/blue]")
        webbrowser.open(url)
    
    # Start uvicorn server
    try:
        import uvicorn
        from ...api.main import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except ImportError:
        console.print("[red]❌ Error: uvicorn not installed[/red]")
        console.print("[yellow]Install with: pip install uvicorn fastapi[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error starting server: {e}[/red]")


if __name__ == '__main__':
    cli()
