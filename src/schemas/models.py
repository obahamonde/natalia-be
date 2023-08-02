
import os
from datetime import datetime

import openai
from aiofauna import *
from aiofauna.llm.llm import FunctionType, LLMStack, function_call
from aiofauna.llm.schemas import Message, Role
from aiofauna.utils import handle_errors, setup_logging
from click import style
from jinja2 import Template

from src.tools.content import CreateImageRequest

from ..helpers.formaters import markdown

previous = """
Conversation:
{{ title }}

Previous messages exchanged with {{ user }}:

{% for message in messages %}
    
    {{ message.role }}:

    {{ message.content }}

{% endfor %}
"""


BucketType = Literal["image", "audio", "video", "assets","code"]
llm = LLMStack(base_url=os.environ["PINECONE_URL"], headers={"api-key": os.environ["PINECONE_API_KEY"]})

class ChatMessage(FaunaModel):
    conversation: str = Field(...,description="The conversation id.",index=True)
    role:Role = Field(...,description="The role of the message.")
    content:str = Field(...,description="The content of the message.")
    
class Namespace(FaunaModel):
    messages: List[str] = Field(default_factory=list)
    title: str = Field(default="[New Conversation]", index=True)
    user: str = Field(..., index=True)

    @handle_errors
    async def set_title(self,text:str):
        response = await llm.chat(text=text,context=f"You are a conversation titles generator, you will generate this conversation title based on the  user first prompt. FIRST PROMPT: {text}")
        return await self.update(self.ref,title=response) #type:ignore
        
    
    @handle_errors 
    async def chat_with_persistence(self,text:str,context:str="You are a helpful assistant"):
        response = await llm.chat_with_memory(text=text,context=context,namespace=self.ref)
        user_message = await ChatMessage(role="user",content=text,conversation=self.ref).save()
        assistant_message = await ChatMessage(role="assistant",content=response,conversation=self.ref).save()
        await self.update(self.ref,messages=self.messages+[user_message.ref,assistant_message.ref]) #type:ignore
        return await ChatMessage.find_many(conversation=self.ref)
        
    
    @handle_errors
    async def chat_premium(self,text:str):
        context = Template(previous).render(
            title=self.title,
            user=self.user,
            messages=(await ChatMessage.find_many(limit=4,conversation=self.ref))
        )   
        return await self.chat_with_persistence(text,context)
   
class User(FaunaModel):
    """
    Auth0 User, Github User or Cognito User
    """

    email: Optional[str] = Field(default=None, index=True)
    email_verified: Optional[bool] = Field(default=False)
    family_name: Optional[str] = Field(default=None)
    given_name: Optional[str] = Field(default=None)
    locale: Optional[str] = Field(default=None, index=True)
    name: str = Field(...)
    nickname: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default=None)
    sub: str = Field(..., unique=True)
    updated_at: Optional[str] = Field(default=None)

class Upload(FaunaModel):
    """

    S3 Upload Record

    """

    user: str = Field(..., description="User sub", index=True)
    name: str = Field(..., description="File name")
    key: str = Field(..., description="File key", unique=True)
    namespace: str = Field(..., description="File namespace", unique=True)
    bucket: BucketType = Field(..., description="File bucket")
    size: int = Field(..., description="File size", gt=0)
    content_type: str = Field(..., description="File type", index=True)
    lastModified: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Last modified",
        index=True,
    )
    url: Optional[str] = Field(None, description="File url")
   
class DatabaseKey(FaunaModel):
    """

    Fauna Database Key

    """

    user: str = Field(..., unique=True)
    database: str = Field(...)
    global_id: str = Field(...)
    key: str = Field(...)
    secret: str = Field(...)
    hashed_secret: str = Field(...)
    role: str = Field(...)


class BlogPostWebPage(FaunaModel,FunctionType):
    """
    This function relies on image generation API and content generation API to generate a blog post.
    The fields that must be collected from the prompt are `blog_prompt` and `image_prompt`.
    The content of the blog post is generated by the content generation API and the image is generated by the image generation API.
    This function will use the outputs of the image generation API and the content generation API to generate a blog post webpage.
    The webpage must embed the image as the Cover Picture of the BlogPost.
    The content might be in markdown format, html format or mixed format that leads to plain text.
    The Large Language Model must generate the content of the blog post in a comprehensive and concise way.
    This content must be formatted to valid HTML any comment or suggestion pointed by the Large Language Model must be removed from the final result in order
    to generate a valid HTML otherwise it can be embedded inside the Javascript part as a comment.
    The styles of the website must be generated by the Large Language Model using TailwindCSS or Bootstrap via the CDN.
    The final output generated by this function will be a webpage that contains the image and the content of the blog post.
    """
    blog_prompt: str = Field(..., description="User input infered from the prompt that describes the main topic of the blogpost")
    image_prompt: str = Field(default=None, description="User input infered from the prompt that describes the appereance of the image")
    content:Optional[str]=Field(default=None,description="This content must be generated by the Large Language Model according to the function description")
    image:Any=Field(default=None,description="This content must be generated by the Large Language Model according to the function description")
    
    async def run(self):
        image_response = await function_call(self.image_prompt,"You are a image generator, you will generate this image based on the user first prompt. FIRST PROMPT: {self.image_prompt}",functions=[CreateImageRequest])
        if isinstance(image_response,dict):
            image_response = image_response["url"]
        
        self.image = image_response
        blog_post_response = await function_call(self.blog_prompt,"You are a blog post generator, you will generate this blog post must be written in markdown and embed the image generated by the image generator. FIRST PROMPT: {self.blog_prompt}, IMAGE_URL: {self.image}",functions=[BlogPostWebPage])
        self.content = markdown(blog_post_response)
        return await self.save()
