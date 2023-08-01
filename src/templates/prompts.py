from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
  text: str
  user: str
  namespace: str
  context: str
  withRetrieval:bool = Field(default=False)
  withFunctions:bool = Field(default=False)
  withAudio:bool = Field(default=False)

