"""
AI Integration Command for PersonalManager.

This module provides integration with AI services like Claude and Gemini
for enhanced productivity and intelligent assistance.
"""

import json
import sys
import time
from typing import Optional, Dict, Any
from datetime import datetime
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pm.core.config import PMConfig

console = Console()

ai_app = typer.Typer(
    name="ai",
    help="AI-powered assistant integrations",
    no_args_is_help=True
)


@ai_app.command(name='route')
def route(
    query: Optional[str] = typer.Argument(None, help="Query to route to AI"),
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    service: Optional[str] = typer.Option(None, "--service", help="AI service to use (claude, gemini)")
):
    """
    Route queries to AI assistants.

    Examples:
        pm ai route "Help me plan my day"
        pm ai route --service=claude "Review my code"
        pm ai route --json "Analyze project status"
    """
    config = PMConfig()

    # Default service if not specified
    if not service:
        service = 'claude'  # Default to Claude

    # If no query provided, enter interactive mode
    if not query:
        if output_json:
            result = {
                'status': 'failed',
                'command': 'ai.route',
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'Query required in JSON mode',
                    'details': {}
                },
                'data': None,
                'metadata': {
                    'version': '0.1.0',
                    'execution_time': 0.001
                }
            }
            console.print_json(data=result)
            raise typer.Exit(1)

        console.print(Panel.fit(
            f"[bold cyan]AI Assistant ({service})[/bold cyan]\n"
            "Enter your query (or 'exit' to quit):",
            border_style="cyan"
        ))
        query = typer.prompt("Query", type=str)

        if query.lower() == 'exit':
            return

    # Process the query
    try:
        result = _process_ai_query(service, query, config)

        if output_json:
            console.print_json(data=result)
        else:
            _display_ai_response(result)

    except Exception as e:
        console.print(f"[dim]AI query failed: {e}[/dim]")

        if output_json:
            error_result = {
                'status': 'failed',
                'command': 'ai.route',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e),
                    'details': {
                        'service': service,
                        'query': query
                    }
                },
                'data': None,
                'metadata': {
                    'version': '0.1.0',
                    'execution_time': 0.001
                }
            }
            console.print_json(data=error_result)
        else:
            console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@ai_app.command(name='config')
def config_cmd(
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key=value"),
    get_key: Optional[str] = typer.Option(None, "--get", help="Get configuration value"),
    list_all: bool = typer.Option(False, "--list", help="List all AI configurations")
):
    """
    Configure AI service settings.

    Examples:
        pm ai config --list
        pm ai config --set default_service=gemini
        pm ai config --get api_key
    """
    config = PMConfig()

    if list_all:
        _list_ai_config(config)
    elif get_key:
        if get_key == 'claude_api_key':
            value = config.claude_api_key
        elif get_key == 'gemini_api_key':
            value = config.gemini_api_key
        else:
            value = None

        if value:
            # Mask sensitive values
            if 'key' in get_key.lower():
                display_value = '***' + str(value)[-4:] if value else 'Not set'
                console.print(f"{get_key}: {display_value}")
            else:
                console.print(f"{get_key}: {value}")
        else:
            console.print(f"[yellow]Configuration '{get_key}' not found[/yellow]")
    elif set_key:
        console.print("[yellow]Configuration setting not implemented in this version[/yellow]")
        console.print("[dim]Note: Set API keys via environment variables PM_CLAUDE_API_KEY or PM_GEMINI_API_KEY[/dim]")
    else:
        console.print("[yellow]No action specified. Use --list, --get, or --set[/yellow]")


@ai_app.command(name='status')
def status(
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format")
):
    """Check AI service connection status."""
    config = PMConfig()

    services = ['claude', 'gemini']
    status_data = {}

    for service in services:
        is_configured = _check_service_config(service, config)
        status_data[service] = {
            'configured': is_configured,
            'status': 'ready' if is_configured else 'not configured'
        }

    if output_json:
        result = {
            'status': 'success',
            'command': 'ai.status',
            'data': status_data,
            'error': None,
            'metadata': {
                'version': '0.1.0',
                'execution_time': 0.001
            }
        }
        console.print_json(data=result)
    else:
        table = Table(title="AI Service Status", show_header=True)
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Configuration", style="yellow")

        for service, data in status_data.items():
            status_style = "green" if data['configured'] else "red"
            table.add_row(
                service.capitalize(),
                f"[{status_style}]{data['status']}[/{status_style}]",
                "✓ Configured" if data['configured'] else "✗ Not configured"
            )

        console.print(table)


def _process_ai_query(service: str, query: str, config: PMConfig) -> Dict[str, Any]:
    """Process an AI query and return the result."""
    # This is a placeholder implementation
    # In a real implementation, this would call the actual AI service

    if service == 'claude':
        # Check for Claude integration
        if not config.claude_api_key:
            raise ValueError("Claude API key not configured. Run 'pm ai config --set claude.api_key=YOUR_KEY'")

        # Simulate Claude response (in real implementation would call Claude API)
        data = {
            'service': 'claude',
            'query': query,
            'response': f"Claude processing: {query}",
            'tokens_used': len(query.split()) * 10
        }

    elif service == 'gemini':
        # Check for Gemini integration
        if not config.gemini_api_key:
            raise ValueError("Gemini API key not configured. Run 'pm ai config --set gemini.api_key=YOUR_KEY'")

        # Simulate Gemini response (in real implementation would call Gemini API)
        data = {
            'service': 'gemini',
            'query': query,
            'response': f"Gemini processing: {query}",
            'tokens_used': len(query.split()) * 8
        }

    else:
        raise ValueError(f"Unknown AI service: {service}")

    # Return standardized JSON format
    response = {
        'status': 'success',
        'command': 'ai.route',
        'data': data,
        'error': None,
        'metadata': {
            'version': '0.1.0',
            'execution_time': 0.001
        }
    }

    return response


def _display_ai_response(result: Dict[str, Any]):
    """Display AI response in a formatted way."""
    data = result.get('data', {})

    console.print(Panel.fit(
        f"[bold cyan]{data.get('service', 'AI').capitalize()} Response[/bold cyan]",
        border_style="cyan"
    ))

    console.print(f"\n{data.get('response', 'No response')}\n")

    if data.get('tokens_used'):
        console.print(f"[dim]Tokens used: {data['tokens_used']}[/dim]")


def _list_ai_config(config: PMConfig):
    """List all AI-related configurations."""
    table = Table(title="AI Configuration", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    # Show AI configuration
    configs = {
        'claude_api_key': config.claude_api_key,
        'gemini_api_key': config.gemini_api_key,
        'ai_tools_enabled': config.ai_tools_enabled,
        'enable_ai_tools': config.enable_ai_tools
    }

    for key, value in configs.items():
        # Mask sensitive values
        if 'key' in key.lower() or 'token' in key.lower():
            display_value = '***' + str(value)[-4:] if value else 'Not set'
        else:
            display_value = str(value) if value is not None else 'Not set'
        table.add_row(key, display_value)

    console.print(table)


def _check_service_config(service: str, config: PMConfig) -> bool:
    """Check if a service is properly configured."""
    if service == 'claude':
        return config.claude_api_key is not None
    elif service == 'gemini':
        return config.gemini_api_key is not None
    else:
        return False


# Export the AI app for registration
__all__ = ['ai_app']