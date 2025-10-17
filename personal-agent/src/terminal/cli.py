"""Command-line interface for the personal agent."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from dotenv import load_dotenv

from ..llm import LLMFactory
from ..agent import AgentBrain, UserProfile
from config.settings import settings

console = Console()
logger = logging.getLogger(__name__)


class AgentCLI:
    """CLI wrapper for the agent."""

    def __init__(self, brain: AgentBrain):
        """Initialize CLI with agent brain.

        Args:
            brain: AgentBrain instance
        """
        self.brain = brain
        self.running = False

    async def start_interactive(self):
        """Start interactive chat session."""
        self.running = True

        console.print(Panel.fit(
            f"[bold blue]Welcome to {self.brain.user_profile.name}'s Personal Agent![/bold blue]\n"
            f"Type your messages below. Commands:\n"
            f"  /discover - Discover interesting content\n"
            f"  /interests - Manage your interests\n"
            f"  /status - Show agent status\n"
            f"  /help - Show help\n"
            f"  /exit - Exit the agent",
            title="Personal Agent"
        ))

        while self.running:
            try:
                # Get user input
                user_input = await asyncio.to_thread(
                    Prompt.ask,
                    "\n[bold green]You[/bold green]"
                )

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue

                # Process regular message
                console.print("\n[bold blue]Agent[/bold blue]: ", end="")
                response = await self.brain.process_message(user_input)

                # Display response with markdown
                console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Error in interactive session: {e}", exc_info=True)

    async def handle_command(self, command: str):
        """Handle slash commands.

        Args:
            command: Command string
        """
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/exit":
            console.print("[yellow]Goodbye![/yellow]")
            self.running = False

        elif cmd == "/help":
            self.show_help()

        elif cmd == "/status":
            await self.show_status()

        elif cmd == "/discover":
            limit = int(parts[1]) if len(parts) > 1 else 5
            await self.discover_content(limit)

        elif cmd == "/interests":
            if len(parts) == 1:
                self.show_interests()
            elif parts[1] == "add" and len(parts) > 2:
                interest = " ".join(parts[2:])
                self.brain.add_interest(interest)
                console.print(f"[green]Added interest: {interest}[/green]")
            elif parts[1] == "remove" and len(parts) > 2:
                interest = " ".join(parts[2:])
                self.brain.remove_interest(interest)
                console.print(f"[yellow]Removed interest: {interest}[/yellow]")
            else:
                console.print("[red]Usage: /interests [add|remove] <interest>[/red]")

        elif cmd == "/understand":
            console.print("\n[bold blue]Analyzing your interactions...[/bold blue]\n")
            understanding = await self.brain.understand_user()
            console.print(Markdown(understanding))

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            console.print("[yellow]Type /help for available commands[/yellow]")

    def show_help(self):
        """Show help information."""
        help_text = """
# Personal Agent Commands

- **/exit** - Exit the agent
- **/help** - Show this help message
- **/status** - Show agent status and statistics
- **/discover [limit]** - Discover interesting content (default: 5 items)
- **/interests** - Show your interests
- **/interests add <interest>** - Add a new interest
- **/interests remove <interest>** - Remove an interest
- **/understand** - Analyze your interactions for better personalization

Just type normally to chat with your agent!
        """
        console.print(Markdown(help_text))

    async def show_status(self):
        """Show agent status."""
        status = self.brain.get_status()

        table = Table(title="Agent Status", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("User", status["user"])
        table.add_row("Interests", ", ".join(status["interests"]) or "None")
        table.add_row("Topics", ", ".join(status["topics"]) or "None")
        table.add_row("Total Interactions", str(status["memory"]["total_interactions"]))
        table.add_row("Discovered Content", str(status["discovered_content_count"]))

        console.print("\n")
        console.print(table)

    def show_interests(self):
        """Show current interests."""
        interests = self.brain.user_profile.preferences.interests
        topics = self.brain.user_profile.preferences.topics

        console.print("\n[bold]Your Interests:[/bold]")
        if interests:
            for i, interest in enumerate(interests, 1):
                console.print(f"  {i}. {interest}")
        else:
            console.print("  [dim]No interests set yet[/dim]")

        console.print("\n[bold]Your Topics:[/bold]")
        if topics:
            for i, topic in enumerate(topics, 1):
                console.print(f"  {i}. {topic}")
        else:
            console.print("  [dim]No topics set yet[/dim]")

    async def discover_content(self, limit: int = 5):
        """Discover content for the user.

        Args:
            limit: Number of items to discover
        """
        console.print(f"\n[bold blue]Discovering {limit} interesting items for you...[/bold blue]\n")

        items = await self.brain.discover_content(limit)

        if not items:
            console.print("[yellow]No content discovered yet. Try adding some interests first![/yellow]")
            return

        for i, item in enumerate(items, 1):
            console.print(Panel(
                f"[bold]{item.title}[/bold]\n\n"
                f"{item.description or 'No description available'}\n\n"
                f"Type: {item.content_type.value} | Score: {item.score:.2f}",
                title=f"Item {i}"
            ))


@click.group(invoke_without_command=True)
@click.option('--user-id', default='default', help='User ID')
@click.option('--user-name', default='User', help='User name')
@click.option('--data-dir', default='./data', help='Data directory')
@click.pass_context
def main(ctx, user_id, user_name, data_dir):
    """Personal Agent - Your AI co-pilot."""
    if ctx.invoked_subcommand is None:
        # Start interactive mode
        asyncio.run(run_interactive(user_id, user_name, data_dir))


async def run_interactive(user_id: str, user_name: str, data_dir: str):
    """Run interactive CLI session.

    Args:
        user_id: User ID
        user_name: User name
        data_dir: Data directory
    """
    load_dotenv()

    # Configure logging with clean output
    from config.logging_config import setup_logging
    setup_logging(
        level=settings.log_level,
        verbose=False,  # Clean output without timestamps
        log_file=settings.log_file
    )

    # Create LLM
    llm_config = settings.get_llm_config()
    llm = LLMFactory.create(llm_config)

    # Load or create user profile
    data_path = Path(data_dir)
    profile_path = data_path / f"profile_{user_id}.json"

    if profile_path.exists():
        user_profile = UserProfile.load(profile_path)
    else:
        user_profile = UserProfile.create_default(user_id, user_name)

    # Initialize agent brain
    async with llm:
        brain = AgentBrain(llm=llm, user_profile=user_profile, data_dir=data_path)

        # Start CLI
        cli = AgentCLI(brain)
        await cli.start_interactive()

        # Cleanup
        await brain.close()


@main.command()
@click.argument('message')
@click.option('--user-id', default='default', help='User ID')
def chat(message, user_id):
    """Send a single message to the agent."""
    asyncio.run(run_single_message(message, user_id))


async def run_single_message(message: str, user_id: str):
    """Process a single message.

    Args:
        message: Message to send
        user_id: User ID
    """
    load_dotenv()

    llm_config = settings.get_llm_config()
    llm = LLMFactory.create(llm_config)

    data_path = Path('./data')
    profile_path = data_path / f"profile_{user_id}.json"

    if profile_path.exists():
        user_profile = UserProfile.load(profile_path)
    else:
        user_profile = UserProfile.create_default(user_id, "User")

    async with llm:
        brain = AgentBrain(llm=llm, user_profile=user_profile, data_dir=data_path)
        response = await brain.process_message(message)
        console.print(Markdown(response))
        await brain.close()


@main.command()
@click.option('--user-id', default='default', help='User ID')
@click.option('--limit', default=10, help='Number of items to discover')
def discover(user_id, limit):
    """Discover interesting content."""
    asyncio.run(run_discover(user_id, limit))


async def run_discover(user_id: str, limit: int):
    """Discover content.

    Args:
        user_id: User ID
        limit: Number of items
    """
    load_dotenv()

    llm_config = settings.get_llm_config()
    llm = LLMFactory.create(llm_config)

    data_path = Path('./data')
    profile_path = data_path / f"profile_{user_id}.json"

    if profile_path.exists():
        user_profile = UserProfile.load(profile_path)
    else:
        console.print("[yellow]No user profile found. Please run the agent first.[/yellow]")
        return

    async with llm:
        brain = AgentBrain(llm=llm, user_profile=user_profile, data_dir=data_path)
        items = await brain.discover_content(limit)

        for i, item in enumerate(items, 1):
            console.print(Panel(
                f"[bold]{item.title}[/bold]\n\n{item.description or 'No description'}",
                title=f"Item {i}"
            ))

        await brain.close()


if __name__ == "__main__":
    main()
