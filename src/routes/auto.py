import functools
from typing import Any, Callable, List, Optional, Type, Union, cast

from aiofauna import APIServer
from aiofauna.llm import function_call
from aiofauna.llm.llm import Model
from aiofauna.typedefs import FunctionType
from aiohttp import ClientSession
from aiohttp.client_reqrep import ContentDisposition
from boto3 import Session
from jinja2 import Template
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.rules_block import StateBlock
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import MarkdownLexer, get_lexer_by_name

from src.config import credentials
from src.schemas import *
from src.tools import content
from src.tools.content import \
    CreateImageRequest  # pylint: disable=no-name-in-module

from ..services import *

context_template = Template(
    """
    You are Automation Bot, you take user prompt and choose the right function to call to automate what user inquiry consists of.
    The user inquiry is: {{ text }}
    """)

logger = setup_logging(__name__)

class HighlightRenderer(RendererHTML):
    def code_block(self, tokens, idx, options, env):
        token = tokens[idx]
        lexer = get_lexer_by_name(token.info.strip() if token.info else "text")
        formatter = HtmlFormatter()
        return highlight(token.content, lexer, formatter)

def highlight_code(code, name, attrs):
    """Highlight a block of code"""
    lexer = get_lexer_by_name(name)
    formatter = HtmlFormatter()

    return highlight(code, lexer, formatter)

md = MarkdownIt(
            "js-default",
            options_update={
                "html": True,
                "typographer": True,
                "highlight": highlight_code
            },
            renderer_cls=HighlightRenderer,
        )

s3 = session.client("s3", region_name="us-east-1")

def render_markdown(text: str) -> str:
    """Render markdown to html"""
    return md.render(text)


class DeterministicFunction(BaseModel):
    response:Any = Field(..., description="The response returned by the openai function.")
    type: str = Field(..., description="The type of the value returned by the openai function.")

def use_auto(app: APIServer):
    
    @app.get("/api/functions/")
    async def list_functions():
        response = [i.openaischema for i in FunctionType._subclasses]
        return response
    
    
    @app.post("/api/functions")
    async def automate(text:str):
        response = await function_call(text=text,context=context_template.render(text=text))
        return DeterministicFunction(response=response,type=type(response).__name__)
    

    @app.post("/api/content")
    async def create_blogpost(request:GenerateContentRequest):
        """Creates a blogpost from a blog prompt and an image prompt"""
        blogpost_webpage = BlogPostWebPage(
            **request.dict()
        )
        async with ClientSession() as session:
            async with session.get(blogpost_webpage.image) as resp: # type: ignore
                res = await resp.read()
                s3.put_object(
                    Bucket="aiofauna-images",
                    Key=f"{blogpost_webpage.user}/{blogpost_webpage.title}.png", # type: ignore
                    Body=res,
                    ACL="public-read",
                    ContentType="image/png"
                )
                blogpost_webpage.image = f"https://s3.amazonaws.com/aiofauna-images/{blogpost_webpage.user}/{blogpost_webpage.title}.png"
                await blogpost_webpage.save()
        return await blogpost_webpage.run()
    
    @app.get("/api/content")
    async def list_content(user:str)->List[BlogPostWebPage]:
        """List all the content generated by a user"""
        response = await BlogPostWebPage.find_many(user=user)
        logger.info(response)
        for i in response:
            if i.content is not None:
                i.content = render_markdown(i.content)
        return response
    
    @app.delete("/api/content")
    async def delete_content(id:str)->bool:
        """Deletes all the content generated by a user"""
        return await BlogPostWebPage.delete(id)

    @app.post("/api/upload")
    async def upload_image(request:Request):
        """Uploads an asset to S3"""
        asset = await UploadRequest.from_request(request)
        s3.put_object(
            Bucket=asset.bucket_name,
            Key=asset.key,
            Body=asset.file.file.read(),
            ACL="public-read",
            ContentType=asset.file.content_type
        )
        url = f"https://s3.amazonaws.com/{asset.bucket_name}/{asset.key}"
        return await Upload(
            user=asset.user,
            name=asset.file.filename,
            key=asset.key,
            bucket=asset.bucket,
            size=asset.size,
            content_type=asset.file.content_type,
            url=url
        ).save()
    
    return app