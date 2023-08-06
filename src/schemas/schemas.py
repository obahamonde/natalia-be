from aiofauna.typedefs import *
from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    text: str
    user: str
    namespace: str
    context: str
    withRetrieval: bool = Field(default=False)
    withFunctions: bool = Field(default=False)
    withAudio: bool = Field(default=False)


class GenerateContentRequest(BaseModel):
    blog_prompt: str
    image_prompt: str
    user: str
    namespace: str

class FunctionRequest(BaseModel):
    text:str
    namespace:str