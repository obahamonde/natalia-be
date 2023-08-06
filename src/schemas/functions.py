import asyncio
from aiofauna.typedefs import FunctionType
from aiofauna import FaunaModel
from typing import *
from pydantic import BaseModel, Field
from aiofauna.llm import LLMStack, function_call
from src.tools.content import CreateImageRequest
from src.services import session
from aiohttp import ClientSession
from uuid import uuid4

llm = LLMStack()
s3 = session.client("s3", region_name="us-east-1")

class PromptEngineer(FunctionType):
	"""Emulates a prompts engineer, building multiple prompts from a single prompt to generate a prompt layer data structure"""
	user_prompt: str = Field(..., description="The user prompt")
	title_prompt: Optional[str] = Field(default=None, description="The title prompt")
	subtitle_prompt: Optional[str] = Field(default=None, description="The subtitle prompt")
	image_prompt: Optional[str] = Field(default=None, description="The image prompt")
	content_prompt: Optional[str] = Field(default=None, description="The content prompt")

	async def get_title(self):
		self.title_prompt = await llm.chat(text=self.title_prompt, context="You are a Prompt Engineer that generates a Blog Post Title Prompt")
		return self

	async def get_subtitle(self):
		self.subtitle_prompt = await llm.chat(text=self.subtitle_prompt, context="You are a Prompt Engineer that generates a Blog Post Subtitle Prompt")
		return self

	async def get_image(self):
		self.image_prompt = await llm.chat(text=self.image_prompt, context="You are a Prompt Engineer that generates a Blog Post Image Prompt")
		return self

	async def get_content(self):
		self.content_prompt = await llm.chat(text=self.content_prompt, context="You are a Prompt Engineer that generates a Blog Post Content Prompt")
		return self

	async def run(self):
		await asyncio.gather(self.get_title(), self.get_subtitle(), self.get_image(), self.get_content())
		return f"""
		# Prompt Engineer
		## User Prompt: {self.user_prompt}
		## Title Prompt: {self.title_prompt}
		## Subtitle Prompt: {self.subtitle_prompt}
		## Image Prompt: {self.image_prompt}
		## Content Prompt: {self.content_prompt}
		"""



class Post(FaunaModel, FunctionType):
	"""A Blog Post"""
	title: str = Field(..., description="The title of the blog post")
	subtitle: str = Field(..., description="The subtitle of the blog post")
	image: str = Field(..., description="The image of the blog post")
	content: str = Field(..., description="The content of the blog post")
	
	async def run(self):
		self.title = await llm.chat(text=self.title, context="You are a Blog Post Title Generator")
		self.subtitle = await llm.chat(text=self.subtitle, context="You are a Blog Post Subtitle Generator")
		image = await CreateImageRequest(prompt=self.image).run()
		self.content = await llm.chat(text=self.content, context="You are a Blog Post Content Generator, In Markdown Format")
		async with ClientSession() as session:
			async with session.get(image) as resp:  # type: ignore
				res = await resp.read()
				id_ = str(uuid4())
				s3.put_object(
					Bucket="images-aiofauna",
					Key=f"{id_}.png",  # type: ignore
					Body=res,
					ACL="public-read",
					ContentType="image/png",
				)
				self.image = f"https://s3.amazonaws.com/aiofauna-images/{id_}.png"
				return await self.save()
		
		