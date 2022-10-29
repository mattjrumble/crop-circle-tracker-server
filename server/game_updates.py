from datetime import datetime, timedelta
from logging import getLogger

from server import database
from server.constants import GAME_UPDATE_DAY, GAME_UPDATE_TIME, GAME_UPDATE_GRACE_PERIOD_SECONDS, TIMEZONE
from server.endpoints import CACHE


logger = getLogger('uvicorn')


def last_update_dt() -> datetime:
    """
    Return the datetime of the last game update.
    """
    now = datetime.now(tz=TIMEZONE)

    if now.weekday() > GAME_UPDATE_DAY:
        post_update = True
    elif now.weekday() == GAME_UPDATE_DAY and now.time() >= GAME_UPDATE_TIME:
        post_update = True
    else:
        post_update = False

    if post_update:
        days_since_update = now.weekday() - GAME_UPDATE_DAY
    else:
        days_since_update = 7 - (GAME_UPDATE_DAY - now.weekday())

    return datetime.combine(date=now - timedelta(days=days_since_update), time=GAME_UPDATE_TIME, tzinfo=TIMEZONE)


def in_update_period() -> bool:
    """
    Determine whether it is currently the weekly game update time plus/minus a grace period.
    """
    now = datetime.now(tz=TIMEZONE)
    last_update = last_update_dt()
    seconds_since_last_update = (now - last_update).total_seconds()
    seconds_until_next_update = (last_update + timedelta(weeks=1) - now).total_seconds()
    # Check if we're just after the previous game update
    if seconds_since_last_update <= GAME_UPDATE_GRACE_PERIOD_SECONDS:
        return True
    # Check if we're just before the next game update
    if seconds_until_next_update <= GAME_UPDATE_GRACE_PERIOD_SECONDS:
        return True
    return False


def recalculate():
    logger.info('Starting recalculating in_update_period...')
    CACHE['in_update_period'] = in_update_period()
    logger.info('Finished recalculating in_update_period')


async def purge_sightings():
    """
    Remove sightings from before the previous game update, since these sightings are now completely invalid.
    """
    logger.info('Purging sightings...')
    result = await database.remove_old_sightings(dt=last_update_dt())
    logger.info('Purged %s sightings', result)
