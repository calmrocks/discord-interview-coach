
GAME_CONFIGS = {
    'truth_dare': {
        'name': 'Truth or Dare',
        'description': 'Classic Truth or Dare game!',
        'min_players': 1,
        'max_players': 10,
        'truths': [
            "What's your biggest fear?",
            "What's the most embarrassing thing you've done?",
            "What's the worst gift you've ever received?",
            "What's your biggest pet peeve?",
            "What's the most childish thing you still do?",
            "What's your guilty pleasure?",
            "What's the worst date you've ever been on?",
            "What's your most awkward moment?",
            "If you could trade lives with someone in this room, who would it be?",
            "What's the worst trouble you got into at school?",
            "What's your biggest regret?",
            "What's the weirdest dream you've ever had?",
            "What's your most unusual talent?",
            "What's the last lie you told?",
            "What's your biggest secret that you've never told anyone?"
        ],
        'dares': [
            "Do your best impression of another player",
            "Sing a song of your choice",
            "Dance without music for 30 seconds",
            "Let another player post anything they want on your social media",
            "Call your crush/partner and tell them a joke",
            "Speak in an accent for the next three rounds",
            "Do 10 push-ups right now",
            "Let the group give you a new hairstyle",
            "Eat a spoonful of hot sauce",
            "Text your parent/sibling something silly",
            "Show the most embarrassing photo on your phone",
            "Switch clothes with the player to your right",
            "Do your best celebrity impression",
            "Let someone draw on your face",
            "Make up a short rap about someone in the room"
        ]
    },
    'word_guess': {
        'name': 'Word Guess',
        'description': 'Guess the word from the given hint!',
        'min_players': 1,
        'max_players': 8,
        'max_rounds': 5,
        'commands': {
            '/quit': 'Quit the current game',
            '/skip': 'Skip the current word',
            '/score': 'Show current scores',
            '/help': 'Show available commands'
        },
        'words': [
            {
                'word': 'python',
                'hints': [
                    'It is a programming language',
                    'It is named after a snake',
                    'It uses indentation for blocks'
                ]
            },
            {
                'word': 'coffee',
                'hints': [
                    'It is a popular beverage',
                    'It contains caffeine',
                    'Many people drink it in the morning'
                ]
            },
            {
                'word': 'pizza',
                'hints': [
                    'It is a popular food',
                    'It is usually round',
                    'Often topped with cheese and tomato sauce'
                ]
            },
            {
                'word': 'computer',
                'hints': [
                    'An electronic device',
                    'Used for processing data',
                    'Has a keyboard and screen'
                ]
            },
            {
                'word': 'elephant',
                'hints': [
                    'It is a large animal',
                    'Has a long trunk',
                    'Found in Africa and Asia'
                ]
            },
            {
                'word': 'umbrella',
                'hints': [
                    'Used on rainy days',
                    'Keeps you dry',
                    'Opens and closes'
                ]
            },
            {
                'word': 'bicycle',
                'hints': [
                    'Has two wheels',
                    'Human-powered transport',
                    'You need to pedal it'
                ]
            },
            {
                'word': 'rainbow',
                'hints': [
                    'Appears after rain',
                    'Has multiple colors',
                    'Arc shape in the sky'
                ]
            }
        ],
        'scoring': {
            'correct_first_try': 3,    # Points for correct guess without hints
            'correct_second_try': 2,    # Points after first hint
            'correct_third_try': 1,     # Points after second hint
            'skip_penalty': -1          # Points deducted for skipping
        },
        'game_rules': {
            'hints_allowed': 3,         # Maximum number of hints per word
            'guess_time': 30,           # Seconds allowed for each guess
            'skip_allowed': True,       # Whether skipping is allowed
            'case_sensitive': False     # Whether guesses are case sensitive
        }
    },
    'mirror_match': {
        'name': 'Mirror Match',
        'description': 'Match the Trendsetter\'s preferences to score points!',
        'min_players': 1,
        'max_players': 8,
        'questions': [
            # Lifestyle Preferences
            {
                'question': 'Do you prefer tea or coffee?',
                'options': ['Tea', 'Coffee']
            },
            {
                'question': 'Are you a morning person or night owl?',
                'options': ['Morning person', 'Night owl']
            },
            {
                'question': 'Do you prefer working from home or office?',
                'options': ['Home', 'Office']
            },

            # Entertainment
            {
                'question': 'Movies: Action or Comedy?',
                'options': ['Action', 'Comedy']
            },
            {
                'question': 'Gaming: Single player or Multiplayer?',
                'options': ['Single player', 'Multiplayer']
            },
            {
                'question': 'Music: Live concerts or Studio recordings?',
                'options': ['Live concerts', 'Studio recordings']
            },

            # Food & Dining
            {
                'question': 'Do you prefer spicy or mild food?',
                'options': ['Spicy', 'Mild']
            },
            {
                'question': 'Sweet or Savory snacks?',
                'options': ['Sweet', 'Savory']
            },
            {
                'question': 'Fast food or Fine dining?',
                'options': ['Fast food', 'Fine dining']
            },

            # Social Preferences
            {
                'question': 'Small gatherings or Big parties?',
                'options': ['Small gatherings', 'Big parties']
            },
            {
                'question': 'Text or Call?',
                'options': ['Text', 'Call']
            },
            {
                'question': 'Plan ahead or Go with the flow?',
                'options': ['Plan ahead', 'Go with the flow']
            },

            # Travel & Adventure
            {
                'question': 'Beach vacation or Mountain retreat?',
                'options': ['Beach', 'Mountain']
            },
            {
                'question': 'International or Domestic travel?',
                'options': ['International', 'Domestic']
            },
            {
                'question': 'Hotel or Camping?',
                'options': ['Hotel', 'Camping']
            },

            # Shopping
            {
                'question': 'Online shopping or In-store shopping?',
                'options': ['Online', 'In-store']
            },
            {
                'question': 'Brand names or Budget friendly?',
                'options': ['Brand names', 'Budget friendly']
            },

            # Technology
            {
                'question': 'iOS or Android?',
                'options': ['iOS', 'Android']
            },
            {
                'question': 'Desktop or Laptop?',
                'options': ['Desktop', 'Laptop']
            },

            # Lifestyle
            {
                'question': 'City life or Countryside?',
                'options': ['City', 'Countryside']
            },
            {
                'question': 'Early dinner or Late dinner?',
                'options': ['Early', 'Late']
            },
            {
                'question': 'Read news online or Traditional newspaper?',
                'options': ['Online news', 'Traditional newspaper']
            },

            # Personal Habits
            {
                'question': 'Shower in morning or Evening?',
                'options': ['Morning', 'Evening']
            },
            {
                'question': 'Exercise indoor or Outdoor?',
                'options': ['Indoor', 'Outdoor']
            },
            {
                'question': 'Save money or Spend now?',
                'options': ['Save', 'Spend']
            }
        ],
        'scoring': {
            'correct_match': 1,
            'perfect_score': 5,
            'bonus_threshold': 8  # Bonus point if player gets 8 or more correct
        }
    }
}