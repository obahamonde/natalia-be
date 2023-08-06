import functools
from celery import Celery
from ..config import env

app = Celery(__name__,backend=env.REDIS_URL,broker=env.REDIS_URL)

def task(func):
    """Decorator to defer the execution of a function to a Celery Worker"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app.send_task(func.__name__, args=args, kwargs=kwargs)
    return wrapper