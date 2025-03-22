from .base_game import BaseGame
import discord
import random
import logging

logger = logging.getLogger(__name__)

class WordGuess(BaseGame):
    GAME_NAME = "word-guess"
    GAME_DESCRIPTION = "Guess the word from the given hint!"
    MIN_PLAYERS = 3

    @property
    def name(self) -> str:
        return self.GAME_NAME

    @property
    def description(self) -> str:
        return self.GAME_DESCRIPTION

    @property
    def min_players(self) -> int:
        return self.MIN_PLAYERS

    def __init__(self, bot, players, guild):
        super().__init__(bot, players, guild)
        self.current_word = None
        self.guesses = {}
        self.round_number = 0
        self.max_rounds = 5

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

    async def end_game(self):
        """End the game and show final scores"""
        await self.channel.send("Game Over! Thanks for playing!")
        # Show final scores here if implemented
        await super().end_game()

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
