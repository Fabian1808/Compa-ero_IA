from app.database import Base, engine
import asyncio
import sqlite3

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('Tablas creadas en transaction')

asyncio.run(create_tables())

conn = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables after create_all:', tables)
if tables:
    for t in tables:
        cursor.execute(f'PRAGMA table_info({t[0]})')
        cols = cursor.fetchall()
        print(t[0], [c[1] for c in cols])