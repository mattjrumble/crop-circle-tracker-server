import aiosqlite

from server.constants import DATABASE_FILENAME


async def initialize():
    async with aiosqlite.connect(DATABASE_FILENAME) as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS sightings '
            '(row_id integer primary key, world integer, location integer, dt text)'
        )
        await db.commit()


async def insert_sighting(world, location, dt):
    async with aiosqlite.connect(DATABASE_FILENAME) as db:
        await db.execute('INSERT INTO sightings (world, location, dt) VALUES (?, ?, ?)', (world, location, dt))
        await db.commit()


async def select_sightings():
    async with aiosqlite.connect(DATABASE_FILENAME) as db:
        return await db.execute_fetchall('SELECT row_id, world, location, dt FROM sightings ORDER BY world, dt')


async def remove_sighting(row_id):
    async with aiosqlite.connect(DATABASE_FILENAME) as db:
        await db.execute('DELETE FROM sightings WHERE row_id = ?', (row_id,))
        await db.commit()


async def remove_old_sightings(dt):
    """
    Remove sightings older than the given datetime. Return the number of sightings deleted.
    """
    async with aiosqlite.connect(DATABASE_FILENAME) as db:
        cursor = await db.execute('DELETE FROM sightings WHERE dt < ?', (dt,))
        await db.commit()
        return cursor.rowcount
