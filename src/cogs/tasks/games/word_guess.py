from .base_game import BaseGame
from src.config.game_config import GAME_CONFIGS
import discord
import random
import logging
import asyncio

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

            self.scores = {player.id: 0 for player in players}
            self.current_round = 0
            self.current_word = None
            self.hints_used = 0
            self.game_active = True
            logger.debug("WordGuess initialization complete")
        except Exception as e:
            logger.error(f"Error in WordGuess initialization: {e}", exc_info=True)
            raise

    async def display_scores(self):
        score_message = "**Current Scores:**\n"
        for player_id, score in self.scores.items():
            player = next((p for p in self.players if p.id == player_id), None)
            player_name = player.name if player else "Unknown Player"
            score_message += f"{player_name}: {score} points\n"
        await self.channel.send(score_message)

    async def process_command(self, command, player_id):
        if command == '/quit':
            self.game_active = False
            await self.channel.send("Game ended by player.")
            return True
        elif command == '/skip':
            await self.channel.send(f"Word skipped. The word was: {self.current_word['word']}")
            self.scores[player_id] += self._config['scoring']['skip_penalty']
            return True
        elif command == '/score':
            await self.display_scores()
            return False
        elif command == '/help':
            help_text = "**Available commands:**\n"
            for cmd, desc in self._config['commands'].items():
                help_text += f"{cmd}: {desc}\n"
            await self.channel.send(help_text)
            return False
        return False

    def select_random_word(self):
        return random.choice(self._config['words'])

    async def play_round(self):
        if not self.game_active:
            return False

        self.current_word = self.select_random_word()
        word_to_guess = self.current_word['word']
        self.hints_used = 0

        round_message = (
            f"**Round {self.current_round + 1}**\n"
            f"Word to guess: `{'_ ' * len(word_to_guess)}`\n"
            f"Length: {len(word_to_guess)} letters"
        )
        await self.channel.send(round_message)

        def check(message):
            return (
                    message.channel == self.channel and
                    message.author in self.players
            )

        while self.hints_used <= self._config['game_rules']['hints_allowed']:
            try:
                guess_message = await self.bot.wait_for('message', timeout=30.0, check=check)
                guess = guess_message.content.strip().lower()
                player_id = guess_message.author.id

                if guess.startswith('/'):
                    if await self.process_command(guess, player_id):
                        return self.game_active

                if guess.lower() == word_to_guess.lower():
                    points = self._config['scoring'][f'correct_{["first", "second", "third"][self.hints_used]}_try']
                    self.scores[player_id] += points
                    await self.channel.send(f"Correct! {guess_message.author.name} gets {points} points!")
                    return True

                if self.hints_used < len(self.current_word['hints']):
                    await self.channel.send(f"Hint {self.hints_used + 1}: {self.current_word['hints'][self.hints_used]}")
                    self.hints_used += 1
                else:
                    await self.channel.send(f"No more hints! The word was: {word_to_guess}")
                    return True

            except asyncio.TimeoutError:
                await self.channel.send("Time's up! Moving to next round...")
                return True

        return True

    async def start_game(self):
        """Start the Word Guess game"""
        logger.info("=== Starting Word Guess Game ===")
        await super().start_game()

        logger.info(f"Game started with {len(self.players)} players")
        logger.info(f"Players: {[p.name for p in self.players]}")

        try:
            await self.channel.send("Welcome to Word Guess Game!\nType /help for available commands")

            while (self.current_round < self._config['max_rounds'] and
                   self.game_active):
                if not await self.play_round():
                    break
                self.current_round += 1

            await self.end_game()
        except Exception as e:
            logger.error(f"Error in Word Guess game: {e}", exc_info=True)
            raise

    async def end_game(self, forced=False):
        """End the Word Guess game"""
        if not forced:
            await self.channel.send("**Game Over!**")
            await self.display_scores()

            winner_id = max(self.scores.items(), key=lambda x: x[1])[0]
            winner = next((p for p in self.players if p.id == winner_id), None)
            if winner:
                await self.channel.send(f"🎉 The winner is {winner.name} with {self.scores[winner_id]} points!")

        # Always call parent class end_game
        await super().end_game(forced=forced)