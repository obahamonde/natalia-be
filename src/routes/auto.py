import functools
from typing import Any, Callable, List, Optional, Type, Union, cast

from aiofauna import APIServer
from aiofauna.llm import function_call
from aiofauna.llm.llm import Model
from aiofauna.typedefs import FunctionType
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class DeterministicFunction(BaseModel):
    response:Any = Field(..., description="The response returned by the openai function.")
    type: str = Field(..., description="The type of the value returned by the openai function.")

def use_auto(app: APIServer):
    
    @app.get("/api/functions/")
    async def list_functions():
        response = [i.openaischema for i in FunctionType._subclasses]
        return response
    
    
    @app.post("/api/functions/")
    async def automate(text:str,context:str):
        response = await function_call(text,context)
        return DeterministicFunction(response=response,type=type(response).__name__)
    return app