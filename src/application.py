from aiofauna import APIServer
from aiofauna.json import to_json
from aiohttp.web_response import StreamResponse

from .helpers import *
from .helpers.formaters import MarkdownRenderer
from .routes import *
from .schemas import *
from .services import *
from .templates import *
from .tools import *

previous = Template("""
Conversation:
{{ title }}

Previous messages exchanged with user:

{% for message in messages %}
    
    {{ message.role }}:

    {{ message.content }}

{% endfor %}
""")

def create_app():
    app = APIServer()
    
    @app.post("/api/auth")
    async def auth_endpoint(request:Request):
        token = request.headers.get("Authorization", "").split("Bearer ")[-1]
        user_dict = await auth.update_headers({"Authorization": f"Bearer {token}"}).get("/userinfo") 
        user = User(**user_dict)
        response = await user.save()
        assert isinstance(response, User)
        return response.dict()
    
    @app.get("/api/conversation/new")
    async def conversation_create(user:str):
        return await Namespace(user=user).save() # type:ignore
    @app.get("/api/conversation/get")
    async def conversation_get(id:str):
        conversation = await Namespace.get(id)    
        if conversation.title == "[New Conversation]" and len(conversation.messages) > 0:
            first_prompt = (await ChatMessage.find_many(conversation=id))[0]
            return await conversation.set_title(first_prompt.content)
        return conversation
    
    @app.get("/api/conversation/list")
    async def conversation_list(user:str):
        return await Namespace.find_many(user=user) 

    
    @app.delete("/api/conversation")
    async def conversation_delete(id:str):
        return await Namespace.delete(id)

    async def conversation_title(text:str,id:str):
        conversation_obj = await Namespace.get(id)
        return await conversation_obj.set_title(text)
    
    @app.post("/api/audio")
    async def audio_response(text:str):
        response = await llm.chat(text,"You are a helpful assistant")
        polly = Polly.from_text(response)
        return Response(body=await polly.get_audio(),content_type="application/octet-stream")
    
    @app.post("/api/messages/list")
    async def post_chat(text:str,namespace:str):
        conversation = await Namespace.get(namespace)
        if conversation.title == "[New Conversation]":
            return await conversation.set_title(text)
        return await conversation.chat_premium(text)
    
    @app.get("/api/messages/get")
    async def get_messages(id:str):
        response = await ChatMessage.find_many(conversation=id)
        messages = []
        for message in response:
            messages.append({
                "role":message.role,
                "content":markdown(message.content),
                "ts":message.ts,
                "ref":message.ref
            })
        return messages
    
    @app.post("/api/functions")
    async def functions_endpoint(text:str):
        return to_json(await function_call(text))
        
    @app.post("/api/upload")
    async def upload_endpoint(request:Request):
        return await upload_asset(request)
    
    @app.websocket("/api/ws")
    async def ws_endpoint(ws:WebSocketResponse,namespace:str):
        conversation = await Namespace.get(namespace)
        while True:
            text = await ws.receive_str()
            if conversation.title == "[New Conversation]":
                await conversation.set_title(text)
            context = await ChatMessage.find_many(limit=4,conversation=namespace)
            response = await llm.chat_with_memory(text=text,context=previous.render(title=conversation.title,messages=context ),namespace=namespace)
            md_response = MarkdownRenderer(response)
            await md_response.stream(ws)    # type:ignore 
            user_message = await ChatMessage(role="user",content=text,conversation=namespace).save() # type:ignore
            assistant_message = await ChatMessage(role="assistant",content=response,conversation=namespace).save() # type:ignore
            await conversation.update(conversation.ref, messages=conversation.messages+[user_message.ref,assistant_message.ref])  # type:ignore
        
    return app