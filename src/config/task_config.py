from datetime import time
from .bot_config import DAILY_TIPS_CHANNEL_IDS, TEST_USER_IDS

TASK_CONFIG = {
    'random_questions': {
        'enabled': True,
        'test_user_ids': TEST_USER_IDS,
        'schedule': {
            'type': 'business_hours',  # business_hours, specific_hours, or daily
            'hours': [9, 17],  # start and end hours for business_hours
            'minute_window': 30,  # run within first 30 minutes of each hour
            'interval': 240  # minutes (4 hours)
        }
    },
    'daily_tips': {
        'enabled': True,
        'channel_ids': DAILY_TIPS_CHANNEL_IDS,
        'schedule': {
            'type': 'daily',  # runs once per day
            'hours': [10],    # run at 10 AM
            'minute_window': 30  # run within first 30 minutes
        }
    },
    'game_invites': {
        'enabled': True,
        'schedule': {
            'type': 'specific_hours',
            'hours': [12, 17, 18, 19],  # specific hours to run
            'minute_window': 60,  # run any time within the hour
            'interval': 15  # minutes
        }
    }
}