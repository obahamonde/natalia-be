
import asyncio
from typing import Optional


def backgroundtask(func):
    async def wrapper(*args, **kwargs):
        asyncio.create_task(func(*args, **kwargs))
    return wrapper