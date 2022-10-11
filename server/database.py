import aiosqlite

FILENAME = 'db.sqlite3'


async def initialize():
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS sightings '
            '(row_id integer primary key, world integer, location integer, dt text)'
        )
        await db.commit()


async def insert_sighting(world, location, dt):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute('INSERT INTO sightings (world, location, dt) VALUES (?, ?, ?)', (world, location, dt))
        await db.commit()


async def select_sightings():
    async with aiosqlite.connect(FILENAME) as db:
        return await db.execute_fetchall('SELECT row_id, world, location, dt FROM sightings ORDER BY world, dt')


async def remove_sighting(row_id):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute('DELETE FROM sightings WHERE row_id = ?', (row_id,))
        await db.commit()
