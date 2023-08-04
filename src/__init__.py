from aiofauna import APIServer

from .routes import use_auto, use_chat


def create_app():
    _ = APIServer(client_max_size=2048*2048*10)

    app = use_chat(use_auto(_))

    return app
