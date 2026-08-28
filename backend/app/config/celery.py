"""
Celery asynchronous task worker configuration stub for RailBlock AI.

STATUS: NOT CONNECTED / FUTURE INTEGRATION

The current project executes data processing, ML scoring, and optimization synchronously
or in in-process threads. No background Celery broker/worker is currently active.
"""

CELERY_AVAILABLE = False
CELERY_STATUS = "NOT_CONNECTED"
CELERY_BROKER_URL: str = ""
CELERY_RESULT_BACKEND: str = ""
