from .base_game import BaseGame
import random
import discord
import logging

logger = logging.getLogger(__name__)

class TruthDare(BaseGame):
    GAME_NAME = "truth-or-dare"
    GAME_DESCRIPTION = "Classic Truth or Dare game!"
    MIN_PLAYERS = 1

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
        self.current_player = None
        self.truths = [
            "What's your biggest fear?",
            "What's the most embarrassing thing you've done?",
            # Add more truth questions
        ]
        self.dares = [
            "Do your best impression of another player",
            "Sing a song of your choice",
            # Add more dares
        ]

    async def start_game(self):
        await super().start_game()
        await self.channel.send("Welcome to Truth or Dare! Let's begin!")
        await self.next_turn()

    async def end_game(self):
        """End the game and clean up"""
        await self.channel.send("Game Over! Thanks for playing!")
        await super().end_game()

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
