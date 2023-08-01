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
    namespace: str = Data(...)
    bucket:BucketType = Data(...)
    file: FileField = Data(...)

    class Config:
        arbitrary_types_allowed = True

    @property
    def key(self):
        return f"{self.user}/{self.namespace}/{self.file.filename}"
    
    @property
    def bucket_name(self):
        return f"{self.bucket}-aiofauna"
    
    @handle_errors
    @classmethod
    async def from_request(cls, request: Request):
        params = dict(request.query)
        assert params.keys() >= {"size", "user", "bucket"}
        assert params["bucket"] in ("audio", "image", "video","code","assets")
        _file = await request.post()
        file = _file["file"]
        assert isinstance(file, FileField)
        assert isinstance(file.filename, str)
        obj = cls(
            size=float(params["size"]),
            user=params["user"],
            bucket=params["bucket"],
            file=file,
            namespace=request.match_info["namespace"],
        )
        return obj

class Bucket:
    """
    Amazon Web Services
    """

    async def upload(self, req: Request):
        """
        Upload Endpoint
        """
        request = await UploadRequest.from_request(req)
        s3 = session.client("s3")
        s3.put_object(
                Bucket=request.bucket_name,
                Key=request.key,
                Body=request.file.file.read(),
                ContentType=request.file.content_type,
                ACL="public-read",
            )
        url = f"https://s3.amazonaws.com/{request.bucket_name}/{request.key}"
        response = await Upload(
                user=request.user,
                key=request.key,
                name=request.file.filename,
                namespace=request.namespace,
                bucket=request.bucket,
                size=request.size,
                content_type=request.file.content_type,
                url=url,
            ).save()
        assert isinstance(response, Upload)
        return response


