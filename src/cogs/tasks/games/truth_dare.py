from .base_game import BaseGame
from .game_config import GAME_CONFIGS
import random
import discord
import logging

logger = logging.getLogger(__name__)

class TruthDare(BaseGame):
    def __init__(self, bot, players, guild):
        logger.debug(f"Initializing TruthDare game with {len(players)} players")
        try:
            super().__init__(bot, players, guild)
            logger.debug("BaseGame initialization complete")

            logger.debug("Loading TruthDare config")
            self._config = GAME_CONFIGS['truth_dare']
            logger.debug(f"Config loaded: {self._config}")

            self.current_player = None
            self.truths = self._config['truths']
            self.dares = self._config['dares']
            logger.debug("TruthDare initialization complete")
        except Exception as e:
            logger.error(f"Error in TruthDare initialization: {e}", exc_info=True)
            raise

    @property
    def name(self) -> str:
        logger.debug("Accessing name property")
        return self._config['name']  # Changed from self.config to self._config

    @property
    def description(self) -> str:
        logger.debug("Accessing description property")
        return self._config['description']  # Changed from self.config to self._config

    @property
    def min_players(self) -> int:
        logger.debug("Accessing min_players property")
        return self._config['min_players']  # Changed from self.config to self._config

    @property
    def max_players(self) -> int:
        logger.debug("Accessing max_players property")
        return self._config['max_players']

    async def start_game(self):
        """Start the Truth or Dare game"""
        logger.info("=== Starting Truth or Dare Game ===")
        await super().start_game()

        logger.info(f"Game started with {len(self.players)} players")
        logger.info(f"Players: {[p.name for p in self.players]}")

        try:
            await self.channel.send("Welcome to Truth or Dare!")
            await self.next_turn()
            logger.info("First turn initiated")
        except Exception as e:
            logger.error(f"Error starting Truth or Dare game: {e}", exc_info=True)
            raise

    async def end_game(self, forced=False):
        """End the Truth or Dare game"""
        if not forced:
            # Do any game-specific cleanup or final score display
            await self.channel.send("Thanks for playing Truth or Dare!")

        # Always call parent class end_game
        await super().end_game(forced=forced)

    async def next_turn(self):
        if not self.is_active:
            return

        self.current_player = random.choice(self.players)
        view = TruthDareView(self)  # Create the view
        await self.channel.send(
            f"{self.current_player.mention}'s turn! Choose Truth or Dare:",
            view=view
        )

    async def handle_truth(self):
        question = random.choice(self.truths)
        await self.channel.send(f"Truth for {self.current_player.mention}: {question}")
        await self.next_turn()

    async def handle_dare(self):
        dare = random.choice(self.dares)
        await self.channel.send(f"Dare for {self.current_player.mention}: {dare}")
        await self.next_turn()

class TruthDareView(discord.ui.View):
    def __init__(self, game):
        super().__init__()
        self.game = game

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.green)
    async def truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.game.current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await interaction.response.defer()
        await self.game.handle_truth()
        self.stop()

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.red)
    async def dare_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.game.current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await interaction.response.defer()
        await self.game.handle_dare()
        self.stop()
