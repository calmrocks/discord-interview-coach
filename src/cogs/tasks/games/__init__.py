from .truth_dare import TruthDare
from .word_guess import WordGuess
from .game_config import GAME_CONFIGS

# Map game IDs to game classes
AVAILABLE_GAMES = {
    'truth_dare': TruthDare,
    'word_guess': WordGuess
}