from dotenv import load_dotenv

load_dotenv()
import asyncio
import os
import subprocess
from functools import partial
from pathlib import Path

import click
from aiofauna.faunadb import query as q
from aiohttp.web import run_app
from requests import post

from src import create_app
from src.utils import gen_port, nginx_cleanup

app = create_app()

@click.group()
def cli():
    pass


@cli.command()
@click.option("--port", default=8080)
@click.option("--host", default="0.0.0.0")
@click.option("--prod", default=False)
def run(port, host, prod):
    if not prod:
        subprocess.run(["gunicorn", "main:app", "-k", "aiohttp.worker.GunicornWebWorker","--reload","--bind", f"{host}:{port}"])
    else:
        subprocess.run(["gunicorn", "main:app", "-k", "aiohttp.worker.GunicornWebWorker","--bind", f"{host}:{port}", "--workers", "4", "--threads", "4"])
 
@cli.command()
def build():
    """Build all containers"""
    path = Path(__file__).parent / "containers"
    containers = os.listdir(path)
    for container in containers:
        subprocess.run(["docker", "build", "-t", container, f"{path}/{container}"])


@cli.command()
def prune():
    nginx_cleanup()




app.static()


if __name__ == "__main__":
    cli()
    
    
    
