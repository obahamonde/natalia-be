from aiofauna import APIServer

from .routes import use_auto, use_chat


def create_app():
    _ = APIServer()

    app = use_chat(use_auto(_))    
    
    return app