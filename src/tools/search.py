import asyncio

import aiohttp
from aiofauna import *
from aiofauna.llm.llm import *
from aiohttp import ClientSession
from bs4 import BeautifulSoup


class SearchResult(BaseModel):
    title: str = Field(...)
    url: str = Field(...)


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/90.0.4430.212 Chrome/90.0.4430.212 Safari/537.36"
}

async def search_google(text: str,lang:str="en",limit:int=10) -> List[SearchResult]:
    async with ClientSession(headers=BROWSER_HEADERS) as session:
        async with session.get(
            f"https://www.google.com/search?q={text}&hl={lang}&num={limit}"
        ) as response:
            soup = BeautifulSoup(await response.text(), "html.parser")
            results = soup.find_all("div", attrs={"class": "g"})
            return [
                SearchResult(
                    title=result.find("h3").text, url=result.find("a").get("href")
                )
                for result in results
            ]


class SeoTags(FunctionType):
    """
    Search for a SEO Tags from results of a Google Search.
    """
    query:str = Field(...)
    lang:str = Field(default="en")
    limit:int = Field(default=10)
    results:Optional[List[SearchResult]] = Field(default=None)
    
    async def run(self):
        self.results = await search_google(self.query,self.lang,self.limit)
        async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
            async def fetch_meta_seo_content(url:str, session:ClientSession):
                async with session.get(url) as response:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    response = soup.find_all("meta")
                    return [ meta.get("content") for meta in response if meta.get("name") in ["description","keywords"] ]
            tasks = [fetch_meta_seo_content(result.url, session) for result in self.results]
            self.results = await asyncio.gather(*tasks)
        return self.results