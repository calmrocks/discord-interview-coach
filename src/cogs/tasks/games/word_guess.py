from .base_game import BaseGame
from .game_config import GAME_CONFIGS
import discord
import random
import logging

logger = logging.getLogger(__name__)

class WordGuess(BaseGame):
    def __init__(self, bot, players, guild):
        logger.debug(f"Initializing WordGuess game with {len(players)} players")
        try:
            super().__init__(bot, players, guild)
            logger.debug("BaseGame initialization complete")

            logger.debug("Loading WordGuess config")
            self._config = GAME_CONFIGS['word_guess']
            logger.debug(f"Config loaded: {self._config}")

            self.current_word = None
            self.guesses = {}
            self.round_number = 0
            self.max_rounds = self._config['max_rounds']
            logger.debug("WordGuess initialization complete")
        except Exception as e:
            logger.error(f"Error in WordGuess initialization: {e}", exc_info=True)
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
        await super().start_game()
        await self.channel.send(
            "Welcome to Word Guess!\n"
            "Rules:\n"
            "1. A word will be chosen and a hint will be given\n"
            "2. Players take turns guessing the word\n"
            "3. First player to guess correctly wins the round\n"
            "Game starting soon..."
        )
        await self.start_round()

    async def end_game(self, forced=False):
        """End the Word Guess game"""
        if not forced:
            # Show final scores or game-specific cleanup
            scores = self.get_scores()
            await self.channel.send(f"Final scores:\n{scores}")

        # Always call parent class end_game
        await super().end_game(forced=forced)

    async def start_round(self):
        self.round_number += 1
        view = WordGuessView(self)  # Create the view
        await self.channel.send(
            f"Round {self.round_number} starting!\n"
            "Use the buttons below to play:",
            view=view
        )

class WordGuessView(discord.ui.View):
    def __init__(self, game):
        super().__init__()
        self.game = game

    @discord.ui.button(label="Make Guess", style=discord.ButtonStyle.primary)
    async def guess_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.game.is_active:
            await interaction.response.send_message("The game has ended!", ephemeral=True)
            return

        # Create a modal for the guess
        modal = GuessModal(self.game)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Show Scores", style=discord.ButtonStyle.secondary)
    async def scores_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        scores = self.game.get_scores()
        await interaction.response.send_message(
            f"Current Scores:\n{scores}",
            ephemeral=True
        )

class GuessModal(discord.ui.Modal, title='Make your guess'):
    def __init__(self, game):
        super().__init__()
        self.game = game

    guess = discord.ui.TextInput(
        label='Your guess',
        placeholder='Type your guess here...',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.game.handle_guess(interaction.user, self.guess.value)
        await interaction.response.defer()
