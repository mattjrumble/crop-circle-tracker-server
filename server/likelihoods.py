from collections import defaultdict
from datetime import datetime
from logging import getLogger
from time import time

from server.endpoints import CACHE
from server.locations import LOCATIONS
from server.database import select_sightings, remove_sighting

FIFTEEN_MINUTES = 15 * 60
ESTIMATED_SERVER_LAG_RATE = 5 / FIFTEEN_MINUTES  # i.e. assume up to 5 seconds of server lag every 15 minutes
SERVER_LAG_LIMIT = FIFTEEN_MINUTES
logger = getLogger('uvicorn')


class Sighting:
    def __init__(self, row_id: int, location: int, dt_string: str):
        self.row_id = row_id
        self.location = location
        self.dt = datetime.fromisoformat(dt_string)
        seconds_since_sighting = int((datetime.now() - self.dt).total_seconds())
        start_of_window = (self.location * FIFTEEN_MINUTES) + seconds_since_sighting
        server_lag = min(seconds_since_sighting * ESTIMATED_SERVER_LAG_RATE, SERVER_LAG_LIMIT)
        self.window = RotationWindow(start_of_window, start_of_window + FIFTEEN_MINUTES + server_lag)

    def __repr__(self):
        return f'(Location {self.location} at {self.dt})'


class WindowsDoNotOverlap(Exception):
    pass


class RotationWindow:
    """
    Represent a window in the crop circle rotation. This can be thought of as a section of a ring of CIRCUMFERENCE
    equal to 15 minutes * the number of crop circle locations. The start of the ring is when the crop circle moves
    to location 0.

    Assume the length of any rotation window is < LENGTH / 2 (i.e. we don't have to worry about sections overlapping
    in two different places).
    """
    CIRCUMFERENCE = len(LOCATIONS) * FIFTEEN_MINUTES

    def __init__(self, start, end):
        self.start = int(start % self.CIRCUMFERENCE)
        self.end = int(end % self.CIRCUMFERENCE)

    def __len__(self):
        if self.end > self.start:
            return self.end - self.start
        else:
            return (self.CIRCUMFERENCE - self.end) + self.start

    def get_likelihoods(self) -> dict[int: float]:
        """
        Return a dictionary of locations to likelihoods that the crop circle is in that particular location, based
        on this window.
        """
        start_location, start_offset = divmod(self.start, FIFTEEN_MINUTES)
        end_location, end_offset = divmod(self.end, FIFTEEN_MINUTES)

        if start_location == end_location:
            likelihoods = {start_location: 1.0}
        elif (start_location + 1) % len(LOCATIONS) == end_location:
            likelihoods = {
                start_location: (FIFTEEN_MINUTES - start_offset) / len(self),
                end_location: end_offset / len(self)
            }
        else:
            likelihoods = {start_location: (FIFTEEN_MINUTES - start_offset) / len(self)}
            location = start_location
            while location != end_location:
                location = (location + 1) % len(LOCATIONS)
                likelihoods[location] = FIFTEEN_MINUTES / len(self)
            likelihoods[end_location] = end_offset / len(self)
        return dict(sorted(likelihoods.items()))

    def combine(self, other_window):
        """
        Combine this window with another window to return the (smaller) overlapping window, or raise an
        WindowsDoNotOverlap error if the two window don't overlap.
        """
        # Offset both windows so that this windows's start is at 0. This simplifies the logic.
        offset = self.CIRCUMFERENCE - self.start
        start = 0
        end = (self.end + offset) % self.CIRCUMFERENCE
        other_start = (other_window.start + offset) % self.CIRCUMFERENCE
        other_end = (other_window.end + offset) % self.CIRCUMFERENCE

        if other_start < end:
            start = other_start
            end = min(end, other_end)
        elif other_end < end:
            end = other_end
            if other_start < other_end:
                start = other_start
        else:
            raise WindowsDoNotOverlap()

        # Undo the offset before returning
        return RotationWindow(start-offset, end-offset)


async def recalculate():
    start = time()
    logger.info('Starting recalculating likelihoods...')
    sightings_by_world = await get_sightings()
    likelihoods = {}
    for world, sightings in sightings_by_world.items():
        window, old_sightings = separate_sightings(sightings)
        likelihoods[world] = window.get_likelihoods()
        if old_sightings:
            logger.info('Removing old sightings for world %s: %s', world, old_sightings)
            for sighting in old_sightings:
                await remove_sighting(sighting.row_id)
    logger.info('Updated likelihoods: %s', likelihoods)
    CACHE['likelihoods'] = likelihoods
    end = time()
    logger.info('Finished recalculating likelihoods (took %ss)', str(round(end - start, 2)))


async def get_sightings() -> dict[int, list[Sighting]]:
    sightings_by_world = defaultdict(list)
    for row_id, world, location, dt in await select_sightings():
        sightings_by_world[world].append(Sighting(row_id=row_id, location=location, dt_string=dt))
    return sightings_by_world


def separate_sightings(sightings: list[Sighting]) -> tuple[RotationWindow, list[Sighting]]:
    """
    Separate out the new, consistent sightings from the old/inconsistent ones. Favour the most recent sightings.
    Return a rotation window from the combined consistent sightings, and a list of the old sightings.
    """
    # Go through each sighting, starting with the most recent. Each sighting gives a rotation window of where the
    # crop circle currently is. Keep combining these windows until one doesn't overlap.
    new_sightings, old_sightings = [], []
    consistent = True
    most_accurate_window = None
    for sighting in sorted(sightings, key=(lambda s: s.dt), reverse=True):
        if consistent:
            if most_accurate_window is None:
                most_accurate_window = sighting.window
            else:
                try:
                    most_accurate_window = most_accurate_window.combine(sighting.window)
                except WindowsDoNotOverlap:
                    consistent = False
        if consistent:
            new_sightings.append(sighting)
        else:
            old_sightings.append(sighting)
    return most_accurate_window, old_sightings
