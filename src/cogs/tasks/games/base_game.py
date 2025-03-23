from datetime import datetime, timedelta
import discord
from abc import ABC, abstractmethod
import logging
import asyncio

logger = logging.getLogger(__name__)

class BaseGame(ABC):
    def __init__(self, bot, players, guild):
        self.bot = bot
        self.players = players
        self.guild = guild
        self.channel = None
        self.start_time = None
        self.is_active = False
        self.cleanup_timeout = 300  # 5 minutes default
        self._config = None

    @property
    def name(self) -> str:
        logger.debug("Accessing name property")
        return self._config['name']

    @property
    def description(self) -> str:
        logger.debug("Accessing description property")
        return self._config['description']

    @property
    def min_players(self) -> int:
        logger.debug("Accessing min_players property")
        return self._config['min_players']

    @property
    def max_players(self) -> int:
        logger.debug("Accessing max_players property")
        return self._config['max_players']

    async def setup_channel(self):
        """Create and set up game channel"""
        logger.info("=== Setting up game channel ===")
        logger.info(f"Creating channel for game: {self.name}")
        logger.info(f"Number of players: {len(self.players)}")

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        # Add permissions for players
        for player in self.players:
            logger.info(f"Adding permissions for player: {player.name}")
            overwrites[player] = discord.PermissionOverwrite(read_messages=True)

        channel_name = f"{self.name}-{datetime.now().strftime('%Y%m%d-%H%M')}"
        logger.info(f"Creating channel with name: {channel_name}")

        try:
            self.channel = await self.guild.create_text_channel(
                channel_name,
                overwrites=overwrites
            )
            logger.info(f"Successfully created channel: {self.channel.name} ({self.channel.id})")
            return self.channel
        except Exception as e:
            logger.error(f"Error creating game channel: {e}", exc_info=True)
            raise

    @abstractmethod
    async def start_game(self):
        """Start the game"""
        self.start_time = datetime.now()
        self.is_active = True

    async def stop_game(self):
        """Stop the game early"""
        logger.info(f"Stopping game in channel {self.channel.name}")
        self.is_active = False
        try:
            await self.channel.send("Game has been stopped early.")
            await self.end_game(forced=True)
        except discord.NotFound:
            # Channel already deleted
            pass

    async def end_game(self, forced=False):
        """End the game and clean up"""
        logger.info(f"Ending game in channel {self.channel.name} (forced: {forced})")
        self.is_active = False

        try:
            if forced:
                await self.channel.send(f"Game ended. Channel will be deleted in {self.cleanup_timeout} seconds.")
            else:
                await self.channel.send(f"Game completed! Channel will be deleted in {self.cleanup_timeout} seconds.")
        except discord.NotFound:
            # Channel already deleted
            return

        await self.schedule_cleanup()

    async def schedule_cleanup(self):
        """Schedule channel cleanup"""
        logger.info(f"Scheduling cleanup for channel {self.channel.name} in {self.cleanup_timeout} seconds")
        await asyncio.sleep(self.cleanup_timeout)

        try:
            if self.channel:
                await self.channel.delete()
                logger.info(f"Successfully deleted channel {self.channel.name}")
        except discord.NotFound:
            # Channel already deleted
            logger.info(f"Channel {self.channel.name} was already deleted")
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
