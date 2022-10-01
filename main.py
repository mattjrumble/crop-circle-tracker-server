from logging import getLogger

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from uvicorn import run

from server import database, likelihoods
from server.endpoints import router
from server.log_config import LOG_CONFIG


app = FastAPI(openapi_url=None)
app.include_router(router)
logger = getLogger('uvicorn')


@app.on_event('startup')
async def initialize():
    await database.initialize()


@app.on_event('startup')
@repeat_every(seconds=10, wait_first=False, logger=logger)
async def recalculate():
    await likelihoods.recalculate()


if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8000, log_config=LOG_CONFIG)
