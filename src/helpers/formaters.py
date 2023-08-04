from aiofauna import Request, Response, WebSocketResponse
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import MarkdownLexer, get_lexer_by_name


class MarkdownRenderer(object):
    def __init__(self, text, language=None):
        self.text = text
        self.language = language

    def format(self) -> str:
        if self.language:
            lexer = get_lexer_by_name(self.language)
        else:
            lexer = MarkdownLexer()
        formatter = HtmlFormatter()
        return highlight(self.text, lexer, formatter)

    async def stream(self, websocket: WebSocketResponse):
        await websocket.send_str(self.format())

    async def ssr(self, request: Request):
        response = Response(text=self.format(), content_type="text/html")
        await response.prepare(request)
        return response


def markdown(text: str):
    return MarkdownRenderer(text).format()
