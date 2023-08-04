import json
from dataclasses import dataclass, field
from os import environ

from aiofauna import *
from aiohttp.web_exceptions import HTTPException

from ..schemas.models import User


@dataclass
class AuthClient(APIClient):
    async def user_info(self, token: str):
        try:
            user_dict = await self.update_headers(
                {"Authorization": f"Bearer {token}"}
            ).get("/userinfo")
            assert isinstance(user_dict, dict)
            return await User(**user_dict).save()

        except (AssertionError, HTTPException) as exc:
            return HTTPException(
                text=json.dumps({"status": "error", "message": str(exc)})
            )


auth = AuthClient(
    base_url=environ["AUTH0_URL"], headers={"Content-Type": "application/json"}
)
