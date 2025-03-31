from datetime import time
from .bot_config import DAILY_TIPS_CHANNEL_IDS, GAME_CHANNELS_IDS, TEST_USER_IDS

TASK_CONFIG = {
    'randomquestions': {
        'enabled': True,
        'test_user_ids': TEST_USER_IDS,
        'loop_minutes': 30,
        'allow_multiple_daily': False,
        'schedule': {
            'type': 'all_hours',
            'minute_window': 60  # run within first 30 minutes of each hour
        }
    },
    'dailytips': {
        'enabled': True,
        'channel_ids': DAILY_TIPS_CHANNEL_IDS,
        'loop_minutes': 30,
        'schedule': {
            'type': 'specific_hours',  # runs once per day
            'hours': [10],    # run at 10 AM
            'minute_window': 30  # run within first 30 minutes
        }
    },
    'gameinvites': {
        'enabled': True,
        'channel_ids': GAME_CHANNELS_IDS,
        'loop_minutes': 15,
        'schedule': {
            'type': 'specific_hours',
            'hours': [12, 17, 18, 19, 22],  # specific hours to run
            'minute_window': 60,  # run any time within the hour
            'interval': 1  # minutes
        },
        'game_settings': {
            'player_wait_time': 60,  # seconds to wait for players
            'cleanup_delay': 300,    # seconds to wait before cleaning up
            'min_players': 3
        }
    }
}