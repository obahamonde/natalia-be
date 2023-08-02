
import asyncio
from dataclasses import dataclass, field

from aiofauna import APIClient, APIConfig
from aiofauna.llm.llm import FunctionType

from ..config import env
from ..helpers.utils import nginx_render


@dataclass
class CloudFlare(APIClient):
    """Domain provisioning service"""

    config: APIConfig = field(
        default_factory=lambda: APIConfig(base_url="https://api.cloudflare.com", headers={
            "X-Auth-Email": env.CF_EMAIL,
            "X-Auth-Key": env.CF_API_KEY,
            "Content-Type": "application/json",
        })
    )

    async def provision(self, name: str, port: int):
        """
        Provision a new domain
        """
        try:
            response = await self.fetch(
                f"/client/v4/zones/{env.CF_ZONE_ID}/dns_records", "POST",
                json={
                    "type": "A",
                    "name": name,
                    "content": env.IP_ADDR,
                    "ttl": 1,
                    "priority": 10,
                    "proxied": True,
                },
            )
            assert isinstance(response, dict)
            data = response["result"]
            nginx_render(name=name, port=port)
            return {
                "url": f"https://{name}.aiofauna.com",
                "ip": f"https://{env.IP_ADDR}:{port}",
                "data": data,
            }
        except Exception as exc:
            raise exc

    async def cleanup_(self):
        records = await self.fetch(
            f"/client/v4/zones/{env.CF_ZONE_ID}/dns_records",
        )

        results = records["result"]

        async def delete_record(record):
            await self.delete(
                f"/zones/{env.CF_ZONE_ID}/dns_records/{record['id']}"
            )

        await asyncio.gather(*[delete_record(record) for record in results])

        return results

cf = CloudFlare(base_url="https://api.cloudflare.com", headers={"X-Auth-Email": env.CF_EMAIL, "X-Auth-Key": env.CF_API_KEY, "Content-Type": "application/json"})


class DnsRecord(FunctionType):
    """
    Provisions an A record for a docker container
    on Cloudflare CDN with an ssl certificate
    """
    host:str
    port:int
    
    async def run(self):
        return await cf.provision(self.host, self.port)