from logging import getLogger

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from uvicorn import run

from server import database, game_updates, likelihoods
from server.constants import LOG_CONFIG
from server.endpoints import router


app = FastAPI(openapi_url=None)
app.include_router(router)
logger = getLogger('uvicorn')


@app.on_event('startup')
async def initialize():
    await database.initialize()


@app.on_event('startup')
@repeat_every(seconds=10, logger=logger)
async def recalculate_quick():
    game_updates.recalculate()
    await game_updates.purge_sightings()
    await likelihoods.recalculate()


if __name__ == '__main__':
    run(app, host='0.0.0.0', port=80, log_config=LOG_CONFIG)
