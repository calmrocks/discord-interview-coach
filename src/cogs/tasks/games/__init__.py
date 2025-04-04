from .truth_dare import TruthDare
from .word_guess import WordGuess
from .mirror_match import MirrorMatch

# Map game IDs to game classes
AVAILABLE_GAMES = {
    'truth_dare': TruthDare,
    'word_guess': WordGuess,
    'mirror_match': MirrorMatch
}