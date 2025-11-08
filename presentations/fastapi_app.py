from fastapi import FastAPI, HTTPException, Response, status, Request
from pydantic import BaseModel
from services.link_service import LinkService
import validators
from typing import Callable, Awaitable
import time
from loguru import logger

def create_app() -> FastAPI:
    app = FastAPI()
    short_link_service = LinkService()
     

    class PutLink(BaseModel):
        link: str
    
    def _service_link_request(short_link: str) ->str:
        return f'http://localhost:8000/{short_link}'
    
    def is_valid(link: str):
        if validators.url(link):
            return True
        else:
            return False

    @app.middleware('http')
    async def add_process_time_to_header(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response|None:

        t0 = time.time()
        try:
            response = await call_next(request)
            dt = (time.time() - t0) * 1000
            response.headers['X-Latency'] = str(dt)
            return response
        except Exception as e:
            logger.warning(f"Unhandled exception in {request.method} {request.url}: {str(e)}")


    @app.post('/link')
    def create_link(put_link_request: PutLink) -> PutLink|None:
        try:
            long_link=put_link_request.link

            if long_link[:8]!='https://':
                long_link='https://' + long_link

            if is_valid(long_link)==False:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Link is not valid')
            
            short_link = short_link_service.create_link(long_link)
            return PutLink(link=_service_link_request(short_link))
        except HTTPException:
            logger.warning(f'{put_link_request.link} is not valid link')
    
    @app.get('/{link}')
    def get_link(link: str) -> Response:
        try:
            real_link = short_link_service.get_real_link(link)

            if real_link is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Short link not found')
            
            return Response (status_code=status.HTTP_301_MOVED_PERMANENTLY, headers={'Location': real_link})
        except HTTPException:
            logger.error(f'{link} is not found')
                                
    return app