from typing import *

from aiofauna.utils import handle_errors
from aiohttp.web import FileField, Request
from boto3 import Session
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import Field as Data  # pylint: disable=no-name-in-module

from ..config import credentials, env
from ..schemas import *
from ..schemas.models import BucketType

session = Session(**credentials)


class UploadRequest(BaseModel):
    """
    UploadRequest
        - key:str
        - size:int
        - user:str
        - file:FileField
    """

    size: float = Data(...)
    user: str = Data(...)
    bucket: BucketType = Data(...)
    file: FileField = Data(...)

    class Config:
        arbitrary_types_allowed = True

    @property
    def key(self):
        return f"{self.user}/{self.file.filename}"

    @property
    def bucket_name(self):
        return f"{self.bucket}-aiofauna"


    @classmethod
    async def from_request(cls, request: Request):
        params = dict(request.query)
        assert params.keys() >= {"size", "user", "bucket"}
        assert params["bucket"] in ("audio", "images", "video", "code", "assets")
        _file = await request.post()
        file = _file["file"]
        assert isinstance(file, FileField)
        assert isinstance(file.filename, str)
        obj = cls(
            size=float(params["size"]),
            user=params["user"],
            bucket=params["bucket"],
            file=file
        )
        return obj
