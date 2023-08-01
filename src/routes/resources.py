from aiofauna.utils import handle_errors
from aiohttp.web import FileField, Request

from ..schemas.models import ChatMessage, Namespace, Upload, User
from ..services import Bucket


@handle_errors
async def upload_asset(request:Request):
    s3 = Bucket()
    return await s3.upload(request)