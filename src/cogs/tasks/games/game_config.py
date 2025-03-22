
GAME_CONFIGS = {
    'truth_dare': {
        'name': 'Truth or Dare',
        'description': 'Classic Truth or Dare game!',
        'min_players': 1,
        'max_players': 10,
        'truths': [
            "What's your biggest fear?",
            "What's the most embarrassing thing you've done?",
        ],
        'dares': [
            "Do your best impression of another player",
            "Sing a song of your choice",
        ]
    },
    'word_guess': {
        'name': 'Word Guess',
        'description': 'Guess the word from the given hint!',
        'min_players': 2,
        'max_players': 8,
        'max_rounds': 5,
        'words': []
    }
}