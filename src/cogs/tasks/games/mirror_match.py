from .base_game import BaseGame
from .game_config import GAME_CONFIGS
import discord
import random
import logging
import asyncio
from typing import Dict, Set, List

logger = logging.getLogger(__name__)

class MirrorMatch(BaseGame):
    def __init__(self, bot, players, guild):
        super().__init__(bot, players, guild)
        self._config = GAME_CONFIGS['mirror_match']

        # Game state
        self.trendsetter = None
        self.trendsetter_answers = {}
        self.player_answers = {}
        self.scores = {player.id: 0 for player in players}
        self.current_questions = []
        self.game_phase = 'setup'  # setup, trendsetter, followers, ended

    async def start_game(self):
        """Initialize and start the Mirror Match game"""
        await super().start_game()

        # Select random trendsetter
        self.trendsetter = random.choice(self.players)
        self.current_questions = random.sample(self._config['questions'], 10)

        # Announce game start and roles
        await self.channel.send(
            "🎮 **Mirror Match Started!**\n\n"
            f"👑 **Trendsetter**: {self.trendsetter.mention}\n"
            f"👥 **Followers**: {', '.join(p.mention for p in self.players if p != self.trendsetter)}\n\n"
            "The Trendsetter will answer some questions, and Followers will try to match their answers!"
        )

        # Start the game phases
        await self.trendsetter_phase()

    async def trendsetter_phase(self):
        """Handle the trendsetter's question phase"""
        self.game_phase = 'trendsetter'

        await self.channel.send(
            f"{self.trendsetter.mention}, you are the Trendsetter!\n"
            "I'll send you 10 questions in DMs. Please answer them honestly!"
        )

        try:
            # Send questions to trendsetter via DM
            dm_channel = await self.trendsetter.create_dm()

            for i, question in enumerate(self.current_questions, 1):
                # Create and send question embed
                embed = discord.Embed(
                    title=f"Question {i}/10",
                    description=question['question'],
                    color=discord.Color.blue()
                )

                # Create button view for options
                view = OptionView(question['options'])
                question_msg = await dm_channel.send(embed=embed, view=view)

                # Wait for trendsetter's answer
                try:
                    await view.wait()
                    if view.selected_option is None:
                        await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                        return await self.end_game(forced=True)

                    self.trendsetter_answers[i] = view.selected_option
                    await question_msg.edit(
                        embed=embed.add_field(name="Your answer", value=view.selected_option),
                        view=None
                    )
                except asyncio.TimeoutError:
                    await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                    return await self.end_game(forced=True)

            await self.channel.send("Trendsetter has completed their answers! Moving to the Followers phase...")
            await self.followers_phase()

        except discord.Forbidden:
            await self.channel.send(
                "Unable to send DM to Trendsetter. Please enable DMs and try again!"
            )
            return await self.end_game(forced=True)

class OptionView(discord.ui.View):
    def __init__(self, options: List[str]):
        super().__init__(timeout=30.0)
        self.selected_option = None

        # Create a button for each option
        for option in options:
            self.add_item(OptionButton(option, self))

class OptionButton(discord.ui.Button):
    def __init__(self, option: str, view: OptionView):
        super().__init__(
            label=option,
            style=discord.ButtonStyle.primary
        )
        self.option = option
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_option = self.option
        await interaction.response.send_message(f"You selected: {self.option}", ephemeral=True)
        self.parent_view.stop()