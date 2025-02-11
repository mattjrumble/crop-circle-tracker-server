from server.constants import LOCATIONS_REVERSE_MAPPING


class ValidationError(Exception):
    pass


def validate_post(data: dict) -> (int, int):
    if set(data.keys()) != {'world', 'location'}:
        raise ValidationError('Invalid keys')

    world, location = data['world'], data['location']

    if not isinstance(location, str):
        raise ValidationError('Invalid location type')

    if not isinstance(world, int):
        raise ValidationError('Invalid world type')

    if location not in LOCATIONS_REVERSE_MAPPING.keys():
        raise ValidationError('Invalid location')

    if world < 300 or world >= 600:
        raise ValidationError('Invalid world')

    return world, LOCATIONS_REVERSE_MAPPING[location]
