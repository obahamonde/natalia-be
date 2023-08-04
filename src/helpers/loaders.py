import functools
import io
import time
from pathlib import Path
from typing import (Any, AsyncGenerator, Awaitable, Callable, Dict, List,
                    Optional, Tuple, TypeVar, Union)

from aiofauna.utils import chunker, setup_logging
from aiohttp.web import FileField, Request
from pypdf import PdfReader


async def pdf_reader(request: Request) -> AsyncGenerator[str, None]:
    """Reads a PDF file from the request and returns a list of strings"""
    data = await request.post()
    file = data["file"]
    assert isinstance(file, FileField)
    with io.BytesIO(file.file.read()) as f:
        reader = PdfReader(f)
    for page in reader.pages:
        yield page.extract_text()
