I am going to use this sse endpoint for consuming my function call feature that can call any function :


```python
class FunctionType(BaseModel, ABC):
    _subclasses: List[Type["FunctionType"]] = []

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _schema = cls.schema()
        if cls.__doc__ is None:
            raise ValueError(
                f"FunctionType subclass {cls.__name__} must have a docstring"
            )
        cls.openaischema = {
            "name": cls.__name__,
            "description": cls.__doc__,
            "parameters": {
                "type": "object",
                "properties": _schema["properties"],
                "required": _schema["required"],
            },
        }
        cls._subclasses.append(cls)

    @abstractmethod
    async def run(self) -> Any:
        ...


F = TypeVar("F", bound=FunctionType)


async def parse_openai_response(  # pylint: disable=dangerous-default-value
    response: dict,
    functions: List[
        Type[F]
    ] = FunctionType._subclasses,  # pylint: disable=protected-access
) -> Any:
    """Parse the response from OpenAI and return the result."""
    choice = response["choices"][0]["message"]
    if "function_call" in choice:
        function_call_ = choice["function_call"]
        name = function_call_["name"]
        arguments = function_call_["arguments"]
        for i in functions:
            if i.__name__ == name:
                result = await i.run(i(**json.loads(arguments)))
                break
        else:
            raise ValueError(f"Function {name} not found")
        return result
    return choice["content"]

@handle_errors
async def function_call(  # pylint: disable=dangerous-default-value
    text: str,
    context: Optional[str] = None,
    model: Model = "gpt-4-0613",
    functions: List[
        Type[F]
    ] = FunctionType._subclasses,  # pylint: disable=protected-access
) -> Any:
    """
    Function to call a OpenAI function with given text and context.

    Arguments:
    text -- Input text for the function
    context -- Optional context for the function
    model -- Model to be used. Defaults to "gpt-4-0613"
    functions -- List of function types. Defaults to all subclasses of FunctionType.
    """
    if context is not None:
        messages = [
            {"role": "user", "content": text},
            {"role": "system", "content": context},
        ]
    else:
        messages = [{"role": "user", "content": text}]
    response = await openai.ChatCompletion.acreate(
        model=model, messages=messages, functions=[i.openaischema for i in functions]
    )
    return await parse_openai_response(response, functions=functions)  # type: ignore


import aioredis
from ..config import env

pool = aioredis.Redis(host=env.REDIS_HOST, port=env.REDIS_PORT, db=0, password=env.REDIS_PASSWORD, username="default",encoding="utf-8", decode_responses=True)
	
pubsub = pool.pubsub()


async def function_handler(namespace:str, sse:EventSourceResponse):
    pubsub.subscribe(namespace)
    async for message in pubsub.listen():
        await sse.send(message)




```
 
