from calendar import WEDNESDAY
from datetime import datetime, timedelta, time
from logging import getLogger

from server import database
from server.endpoints import CACHE


UPDATE_DAY = WEDNESDAY
UPDATE_TIME = time(hour=11, minute=30)
UPDATE_GRACE_PERIOD_SECONDS = 30 * 60
logger = getLogger('uvicorn')


def last_update_dt() -> datetime:
    """
    Return the datetime of the last game update.
    """
    now = datetime.now()

    if now.weekday() > UPDATE_DAY:
        post_update = True
    elif now.weekday() == UPDATE_DAY and now.time() >= UPDATE_TIME:
        post_update = True
    else:
        post_update = False

    if post_update:
        days_since_update = now.weekday() - UPDATE_DAY
    else:
        days_since_update = 7 - (UPDATE_DAY - now.weekday())

    return datetime.combine(date=now - timedelta(days=days_since_update), time=UPDATE_TIME)


def in_update_period() -> bool:
    """
    Determine whether it is currently the weekly game update time plus/minus a grace period.
    """
    now = datetime.now()
    last_update = last_update_dt()
    seconds_since_last_update = (now - last_update).total_seconds()
    seconds_until_next_update = (last_update + timedelta(weeks=1) - now).total_seconds()
    # Check if we're just after the previous game update
    if seconds_since_last_update <= UPDATE_GRACE_PERIOD_SECONDS:
        return True
    # Check if we're just before the next game update
    if seconds_until_next_update <= UPDATE_GRACE_PERIOD_SECONDS:
        return True
    return False


def recalculate():
    logger.info('Starting recalculating in_update_period...')
    CACHE['in_update_period'] = in_update_period()
    logger.info('Finished recalculating in_update_period')


async def purge_sightings():
    """
    Remove sightings from before the previous game update, since these sightings are now completely invalid. Assume
    the game update happens weekly at Wednesday 11:30AM UK time.
    """
    logger.info('Purging sightings...')
    result = await database.remove_old_sightings(dt=last_update_dt())
    logger.info('Purged %s sightings', result)
