from datetime import datetime
from logging import getLogger

from fastapi import APIRouter, HTTPException, Depends
from fastapi.routing import APIRoute

from server.authentication import authentication
from server.database import insert_sighting
from server.validators import validate_post, ValidationError

logger = getLogger('uvicorn')


class LoggingRoute(APIRoute):
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request):
            logger.info(
                "Started request from %s '%s %s'. Request body: %s",
                request.client.host,
                request.method,
                request.url.path,
                await request.body()
            )
            response = await original_route_handler(request)
            logger.info(
                "Finished request from %s '%s %s'. Response body: %s",
                request.client.host,
                request.method,
                request.url.path,
                response.body
            )
            return response

        return custom_route_handler


router = APIRouter(route_class=LoggingRoute)
likelihoods_cache = {}


@router.get('/', dependencies=[Depends(authentication)])
async def get():
    return likelihoods_cache


@router.post('/', dependencies=[Depends(authentication)])
async def post(data: dict):
    try:
        world, location = validate_post(data)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await insert_sighting(world=world, location=location, dt=datetime.now())
