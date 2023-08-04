import asyncio
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, List

from aiofauna.typedefs import *
from aiofauna.utils import handle_errors
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ..services.cloudflare import cf
from ..services.docker import DockerService
from ..utils import gen_port

PromptCall = Callable[[str, List[F]], Awaitable[Any]]

docker = DockerService(
    base_url="http://localhost:9898", headers={"Content-Type": "application/json"}
)


class AbstractDocker(BaseModel, ABC):
    port: int = Field(..., description="Port from the container")
    host_port: int = Field(default_factory=gen_port, description="Port to expose")
    image: str = Field(..., description="Image to use")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Extra arguments")

    @abstractmethod
    def payload(self):
        pass


class NginxDocker(FunctionType, AbstractDocker):
    """Create an NGINX instance"""

    def payload(self):
        return {
            "Image": self.image,
            "HostConfig": {
                "PortBindings": {
                    f"{self.port}/tcp": [{"HostPort": str(self.host_port)}]
                }
            },
        }

    @handle_errors
    async def run(self):
        """Run the function"""
        response = await docker.fetch(
            "/containers/create", method="POST", json=self.payload()
        )
        id_ = response["Id"]
        await docker.text(f"/containers/{id_}/start", method="POST")
        await asyncio.sleep(1)
        response = await docker.fetch(f"/containers/{id_}/json", method="GET")
        dns_response = await cf.provision(
            f"{self.image}-{self.host_port}", self.host_port
        )
        return {"container": response, "dns": dns_response}


class CodeServerDocker(FunctionType, AbstractDocker):
    """Creates a CodeServer instance"""

    def payload(self, **kwargs):
        return {
            "Image": self.image,
            "Env": kwargs.get("env_vars", []),
            "HostConfig": {
                "PortBindings": {
                    f"{self.port}/tcp": [{"HostPort": str(self.host_port)}]
                },
                "Binds": [kwargs.get("volume", "")],
            },
        }

    @handle_errors
    async def run(self):
        """Run the function"""
        response = await docker.fetch(
            "/containers/create", method="POST", json=self.payload()
        )
        id_ = response["Id"]
        await docker.text(f"/containers/{id_}/start", method="POST")
        await asyncio.sleep(1)
        response = await docker.fetch(f"/containers/{id_}/json", method="GET")
        dns_response = await cf.provision(
            f"{self.image}-{self.host_port}", self.host_port
        )
        return {"container": response, "dns": dns_response}


class DatabaseDocker(FunctionType, AbstractDocker):
    """Creates a MySQL, Postgres, or MongoDB instance"""

    def payload(self, **kwargs):
        return {
            "Image": self.image,
            "Env": kwargs.get("env_vars", []),
            "HostConfig": {
                "PortBindings": {
                    f"{self.port}/tcp": [{"HostPort": str(self.host_port)}]
                },
                "Binds": [kwargs.get("volume", "")],
            },
        }

    @handle_errors
    async def run(self):
        """Run the function"""
        response = await docker.fetch(
            "/containers/create", method="POST", json=self.payload()
        )
        id_ = response["Id"]
        await docker.text(f"/containers/{id_}/start", method="POST")
        await asyncio.sleep(1)
        response = await docker.fetch(f"/containers/{id_}/json", method="GET")
        dns_response = await cf.provision(
            f"{self.image}-{self.host_port}", self.host_port
        )
        return {"container": response, "dns": dns_response}


class DeleteContainer(FunctionType):
    """Stops and deletes a container"""

    id: str = Field(..., description="Container ID")

    @handle_errors
    async def run(self):
        """Run the function"""
        await docker.text(f"/containers/{self.id}/stop", method="POST")
        await docker.text(f"/containers/{self.id}", method="DELETE")
        return {"message": "Container deleted"}
