import os

from aiofauna.llm.llm import LLMStack

from .auth import *
from .bucket import *
from .cloudflare import *
from .docker import *
from .speech import *
from .pubsub import *

llm = LLMStack(base_url=os.environ.get("PINECONE_URL"), headers={"api-key": os.environ.get("PINECONE_KEY")})  # type: ignore
