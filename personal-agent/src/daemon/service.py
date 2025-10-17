"""Background daemon service that runs continuously."""

import asyncio
import logging
import signal
from pathlib import Path
from typing import Optional
from datetime import datetime

import click
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from ..llm import LLMFactory
from ..agent import AgentBrain, UserProfile
from config.settings import settings
from config.logging_config import setup_logging

logger = logging.getLogger(__name__)


class DaemonService:
    """Background service for continuous agent operations."""

    def __init__(
        self,
        user_id: str = "default",
        data_dir: str = "./data",
        check_interval: int = 30
    ):
        """Initialize daemon service.

        Args:
            user_id: User ID
            data_dir: Data directory
            check_interval: Check interval in minutes
        """
        self.user_id = user_id
        self.data_dir = Path(data_dir)
        self.check_interval = check_interval
        self.scheduler = AsyncIOScheduler()
        self.brain: Optional[AgentBrain] = None
        self.llm = None
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Frame object
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def initialize(self):
        """Initialize the daemon service."""
        logger.info("Initializing daemon service...")

        # Load configuration
        load_dotenv()

        # Create LLM
        llm_config = settings.get_llm_config()
        self.llm = LLMFactory.create(llm_config)
        await self.llm.initialize()

        # Load or create user profile
        profile_path = self.data_dir / f"profile_{self.user_id}.json"

        if profile_path.exists():
            user_profile = UserProfile.load(profile_path)
            logger.info(f"Loaded user profile: {user_profile.name}")
        else:
            user_profile = UserProfile.create_default(self.user_id, "User")
            logger.info("Created default user profile")

        # Initialize agent brain
        self.brain = AgentBrain(
            llm=self.llm,
            user_profile=user_profile,
            data_dir=self.data_dir
        )

        logger.info("Daemon service initialized")

    async def start(self):
        """Start the daemon service."""
        await self.initialize()

        # Schedule periodic tasks
        self.scheduler.add_job(
            self.discover_content_task,
            trigger=IntervalTrigger(minutes=self.check_interval),
            id="discover_content",
            name="Discover interesting content",
            replace_existing=True
        )

        self.scheduler.add_job(
            self.analyze_user_task,
            trigger=IntervalTrigger(hours=6),
            id="analyze_user",
            name="Analyze user preferences",
            replace_existing=True
        )

        # Start scheduler
        self.scheduler.start()
        self.running = True

        logger.info(f"Daemon started. Content discovery every {self.check_interval} minutes.")
        logger.info("Press Ctrl+C to stop.")

        # Run initial discovery
        await self.discover_content_task()

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the daemon service."""
        logger.info("Stopping daemon service...")

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        if self.brain:
            await self.brain.close()

        if self.llm:
            await self.llm.close()

        logger.info("Daemon service stopped")

    async def discover_content_task(self):
        """Periodic task to discover interesting content."""
        try:
            logger.info("Running content discovery task...")

            if not self.brain:
                logger.warning("Brain not initialized")
                return

            items = await self.brain.discover_content(limit=5)

            if items:
                logger.info(f"Discovered {len(items)} content items")
                for i, item in enumerate(items[:3], 1):
                    logger.info(f"  {i}. {item.title} (score: {item.score:.2f})")
            else:
                logger.info("No new content discovered")

        except Exception as e:
            logger.error(f"Error in content discovery task: {e}", exc_info=True)

    async def analyze_user_task(self):
        """Periodic task to analyze user and update preferences."""
        try:
            logger.info("Running user analysis task...")

            if not self.brain:
                logger.warning("Brain not initialized")
                return

            understanding = await self.brain.understand_user()
            logger.info("User analysis completed")
            logger.debug(f"Understanding: {understanding[:200]}...")

            # You could parse the understanding and automatically update preferences here

        except Exception as e:
            logger.error(f"Error in user analysis task: {e}", exc_info=True)

    def get_status(self) -> dict:
        """Get daemon status.

        Returns:
            Status dictionary
        """
        if not self.brain:
            return {"status": "not_initialized"}

        status = self.brain.get_status()
        status.update({
            "daemon_running": self.running,
            "check_interval_minutes": self.check_interval,
            "next_discovery": self.scheduler.get_job("discover_content").next_run_time if self.scheduler.running else None,
        })

        return status


@click.command()
@click.option('--user-id', default='default', help='User ID')
@click.option('--data-dir', default='./data', help='Data directory')
@click.option('--check-interval', default=30, help='Check interval in minutes')
@click.option('--log-level', default='WARNING', help='Log level')
def main(user_id, data_dir, check_interval, log_level):
    """Start the personal agent daemon service."""
    setup_logging(level=log_level, verbose=False)

    daemon = DaemonService(
        user_id=user_id,
        data_dir=data_dir,
        check_interval=check_interval
    )

    asyncio.run(daemon.start())


if __name__ == "__main__":
    main()
