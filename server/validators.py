from server.constants import LOCATIONS


class ValidationError(Exception):
    pass


def validate_post(data):
    if set(data.keys()) != {'world', 'location'}:
        raise ValidationError('Invalid keys')
    world, location = data['world'], data['location']
    if not isinstance(world, int):
        raise ValidationError('Invalid world type')
    if not isinstance(location, int):
        raise ValidationError('Invalid location type')
    if world < 300 or world >= 600:
        raise ValidationError('Invalid world')
    if location not in LOCATIONS.keys():
        raise ValidationError('Invalid location')
    return world, location
