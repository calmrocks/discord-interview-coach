from datetime import time
from .bot_config import DAILY_TIPS_CHANNEL_IDS

TASK_CONFIG = {
    'random_questions': {
        'enabled': True,
        'check_interval': 30,  # minutes
        'business_hours': {
            'start': time(9, 0),
            'end': time(17, 0)
        },
        'cooldown': 14400,  # 4 hours in seconds
    },
    'daily_tips': {
        'enabled': True,
        'channel_ids': DAILY_TIPS_CHANNEL_IDS,
        'send_time': time(10, 0),  # 10 AM
    },
    'game_invites': {
        'enabled': True,
        'check_interval': 15,
        'active_hours': [
            (time(12, 0), time(13, 0)),  # Lunch hour
            (time(17, 0), time(20, 0)),  # After work
        ]
    }
}