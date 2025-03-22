from datetime import time
from .bot_config import DAILY_TIPS_CHANNEL_IDS, TEST_USER_IDS

TASK_CONFIG = {
    'randomquestions': {
        'enabled': False,
        'test_user_ids': TEST_USER_IDS,
        'loop_minutes': 30,
        'schedule': {
            'type': 'business_hours',  # business_hours, specific_hours, or daily
            'hours': [9, 17],  # start and end hours for business_hours
            'minute_window': 30,  # run within first 30 minutes of each hour
            'interval': 240  # minutes (4 hours)
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
        'loop_minutes': 15,
        'schedule': {
            'type': 'specific_hours',
            'hours': [12, 17, 18, 19],  # specific hours to run
            'minute_window': 60,  # run any time within the hour
            'interval': 15  # minutes
        }
    }
}