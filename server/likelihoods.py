from collections import defaultdict
from datetime import datetime
from json import dumps
from logging import getLogger

from server.locations import LOCATIONS
from server.database import select_sightings, remove_sighting, update_likelihoods, remove_orphan_likelihoods

FIFTEEN_MINUTES = 15 * 60
logger = getLogger('uvicorn')


class Sighting:
    def __init__(self, row_id: int, location: int, dt_string: str):
        self.row_id = row_id
        self.location = location
        self.dt = datetime.fromisoformat(dt_string)

    def __repr__(self):
        return f'(Location {self.location} at {self.dt})'


class InconsistentSections(Exception):
    pass


class Section:
    """
    Represent a section of a ring (i.e. the set of numbers modulus LENGTH). In this case, LENGTH is the number of
    seconds it takes for a full crop circle rotation (i.e. for the crop circle to get back to where it started).
    Assume the length of each section is < LENGTH / 2 (i.e. we don't have to worry about sections overlapping in two
    different places).
    """
    LENGTH = len(LOCATIONS) * FIFTEEN_MINUTES

    def __init__(self, start, end):
        self.start = start % self.LENGTH
        self.end = end % self.LENGTH

    def combine(self, other_section):
        """
        Combine this section with another section to return the (smaller) overlapping section, or raise an
        InconsistentSections error if the two sections don't overlap.
        """
        # Offset both sections so that this section's (section 1) start is at 0. This simplifies the logic.
        offset = self.LENGTH - self.start
        start = 0
        end = (self.end + offset) % self.LENGTH
        other_start = (other_section.start + offset) % self.LENGTH
        other_end = (other_section.end + offset) % self.LENGTH

        if other_start < end:
            start = other_start
            end = min(end, other_end)
        elif other_end < end:
            end = other_end
            if other_start < other_end:
                start = other_start
        else:
            raise InconsistentSections()

        # Undo the offset before returning
        return Section(start-offset, end-offset)


async def recalculate():
    logger.debug('Starting recalculate...')
    sightings_by_world = await get_sightings()
    for world, sightings in sightings_by_world.items():
        new_sightings, old_sightings = separate_sightings(sightings)
        if old_sightings:
            logger.debug('Removing old sightings for world %s: %s', world, old_sightings)
            for sighting in old_sightings:
                await remove_sighting(sighting.row_id)
        likelihoods = get_likelihoods(new_sightings)
        logger.debug('Updating likelihoods for world %s: %s', world, likelihoods)
        await update_likelihoods(world, dumps(likelihoods))
    # Removing likelihoods for worlds without any sightings
    await remove_orphan_likelihoods(worlds=list(set(sightings_by_world.keys())))
    logger.debug('Finished recalculate.')


async def get_sightings() -> dict[int, list[Sighting]]:
    sightings_by_world = defaultdict(list)
    for row_id, world, location, dt in await select_sightings():
        sightings_by_world[world].append(Sighting(row_id=row_id, location=location, dt_string=dt))
    return sightings_by_world


def separate_sightings(sightings: list[Sighting]) -> tuple[list[Sighting], list[Sighting]]:
    """
    Separate out the new, consistent sightings from the old, inconsistent ones. Favour the most recent sightings.
    """
    # Go through each sighting, starting with the most recent. Each sighting gives a window of times where the crop
    # circle will move to Location 0. Keep combining these sections until one is inconsistent.
    new_sightings, old_sightings = [], []
    consistent = True
    most_accurate_section = None
    for sighting in sorted(sightings, key=(lambda s: s.dt), reverse=True):
        if consistent:
            new_sightings.append(sighting)
            seconds_until_location_0 = ((len(LOCATIONS) - sighting.location) % len(LOCATIONS)) * FIFTEEN_MINUTES
            section = Section(
                sighting.dt.timestamp() + seconds_until_location_0 - FIFTEEN_MINUTES,
                sighting.dt.timestamp() + seconds_until_location_0 + FIFTEEN_MINUTES
            )
            if most_accurate_section is None:
                most_accurate_section = section
            else:
                try:
                    most_accurate_section = most_accurate_section.combine(section)
                except InconsistentSections:
                    consistent = False
                    old_sightings.append(new_sightings.pop())
        else:
            old_sightings.append(sighting)
    return new_sightings, old_sightings


def get_likelihoods(sightings: list[Sighting]) -> dict[int: float]:
    # For each sighting, there's a moment within the last 15 minutes where the sighting tells us the current location
    # of the crop circle with 100% accuracy. Calculate that location, and the number of seconds since that moment.
    current_dt = datetime.now()
    sightings_plus_moment_info = []
    for sighting in sightings:
        seconds_since_sighting = int((current_dt - sighting.dt).total_seconds())
        seconds_since_moment = seconds_since_sighting % FIFTEEN_MINUTES
        location_at_moment = (sighting.location + int(seconds_since_sighting / FIFTEEN_MINUTES)) % len(LOCATIONS)
        sightings_plus_moment_info.append(
            {'sighting': sighting, 'location': location_at_moment, 'seconds': seconds_since_moment}
        )

    # Sort the sightings by seconds_since_moment. The sighting with the lowest seconds_since_moment is the one
    # that's most useful to us. The current location is either there or in the next location.
    sightings_plus_moment_info = list(sorted(sightings_plus_moment_info, key=(lambda s: s['seconds'])))

    # When there's more than one location, we know that the crop circle is at the later location (i.e. the location
    # given by the sighting with the lowest seconds_since_moment). If there's only one location then there's some
    # uncertainty (the crop circle might be at that location or it might be at the next location), and we calculate
    # a likelihood based on the window of time that's unaccounted for by our sightings.
    location_count = len(set(s['location'] for s in sightings_plus_moment_info))
    if location_count > 1:
        likelihoods = {
            sightings_plus_moment_info[0]['location']: 1.0
        }
    else:
        lowest_seconds_since_moment = sightings_plus_moment_info[0]['seconds']
        highest_seconds_since_moment = sightings_plus_moment_info[-1]['seconds']
        unknown_window = FIFTEEN_MINUTES - (highest_seconds_since_moment - lowest_seconds_since_moment)
        likelihoods = {
            sightings_plus_moment_info[0]['location']:
                1 - lowest_seconds_since_moment / unknown_window,
            (sightings_plus_moment_info[0]['location'] + 1) % len(LOCATIONS):
                lowest_seconds_since_moment / unknown_window
        }

    return likelihoods
