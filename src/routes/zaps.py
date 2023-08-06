from typing import *

from aiofauna.json import to_json
from ..schemas.functions import *
from aiofauna import *
from ..services.pubsub import FunctionQueue
from ..helpers import app



	

def use_zaps(app:APIServer):
	@app.sse("/api/consumer/{namespace}")
	async def function_consumer(namespace:str,sse:EventSourceResponse):
		queue = FunctionQueue(namespace=namespace)
		async for event in queue.sub():
			await sse.send(event)

	@app.post("/api/producer")
	async def function_producer(namespace:str,text:str):
		queue = FunctionQueue(namespace=namespace)
		await queue.pub(message=text)
		return await function_call(text=text,context="You are a function Orchestrator",model="gpt-3.5-turbo-16k-0613")
	return app