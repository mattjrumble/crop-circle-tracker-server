import aiosqlite

FILENAME = 'db.sqlite3'


async def initialize():
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS sightings '
            '(row_id integer primary key, world integer, location integer, dt text)'
        )
        await db.execute('CREATE TABLE IF NOT EXISTS likelihoods (world integer, likelihood_json text)')
        await db.commit()


async def insert_sighting(world, location, dt):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute('INSERT INTO sightings (world, location, dt) VALUES (?, ?, ?)', (world, location, dt))
        await db.commit()


async def select_sightings():
    async with aiosqlite.connect(FILENAME) as db:
        return await db.execute_fetchall('SELECT row_id, world, location, dt FROM sightings ORDER BY world, dt')


async def select_likelihoods():
    async with aiosqlite.connect(FILENAME) as db:
        return await db.execute_fetchall('SELECT world, likelihood_json FROM likelihoods ORDER BY world')


async def update_likelihoods(world, likelihoods_json):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute('INSERT INTO likelihoods (world, likelihood_json) VALUES (?, ?)', (world, likelihoods_json))
        await db.commit()


async def remove_sighting(row_id):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute('DELETE FROM sightings WHERE row_id = ?', (row_id,))
        await db.commit()


async def remove_orphan_likelihoods(worlds):
    async with aiosqlite.connect(FILENAME) as db:
        await db.execute(
            f"DELETE FROM likelihoods WHERE world NOT IN ({','.join('?' * len(worlds))})",
            worlds
        )
        await db.commit()
