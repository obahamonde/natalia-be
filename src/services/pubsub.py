from typing import AsyncGenerator, TypeVar
import aioredis
from aioredis.client import PubSub
from aiofauna.json import to_json
from aiofauna.typedefs import LazyProxy
from aiofauna.utils import setup_logging, handle_errors
from aiofauna.llm import function_call
from ..config import env

T = TypeVar("T")

logger = setup_logging(__name__)

pool = aioredis.Redis.from_url(env.REDIS_URL)

class FunctionQueue(LazyProxy[PubSub]):
	def __init__(self, namespace: str):
		"""Initializes a new FunctionQueue Event Stream to catch function call event results in an asynchronous fashion."""
		self.namespace = namespace
		logger.info(f"Initializing state for {namespace}")
		self.ps = self.__load__()


	def __load__(self):
		"""Lazy loading of the PubSub object."""
		return pool.pubsub()

	
	async def sub(self) -> AsyncGenerator[str, None]:
		"""Subscribes to the PubSub channel and yields messages as they come in."""
		await self.ps.subscribe(self.namespace)
		logger.info(f"Subscribed to {self.namespace}")
		async for message in self.ps.listen():
			try:
				data = message["data"]
				yield data.decode("utf-8")
			except (KeyError, AssertionError, UnicodeDecodeError, AttributeError):
				logger.error(f"Invalid message received: {message}")
				continue
			finally:
				await self.ps.unsubscribe(self.namespace)


	async def _send(self, message: str) -> None:
		"""Protected method to send a message to the PubSub channel."""
		logger.info(f"Sending message to {self.namespace}")
		await pool.publish(self.namespace, message)
		await self.ps.unsubscribe(self.namespace)


	async def pub(self, message:str)->None:
		"""Public method to send a function call result to the PubSub channel."""
		response = await function_call(text=message,context="You are a function Orchestrator",model="gpt-3.5-turbo-16k-0613")
		logger.info(f"Function call result: {response}")
		await self._send(to_json(response))
		logger.info(f"Message sent to {self.namespace}")
		await self.ps.unsubscribe(self.namespace)
		logger.info(f"Unsubscribed from {self.namespace})")
