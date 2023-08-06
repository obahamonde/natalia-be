from aiofauna import APIServer

from .routes import *


def create_app():
    _ = APIServer(client_max_size=2048 * 2048 * 10)

    app = use_chat(use_auto(use_zaps(_)))

    return app
