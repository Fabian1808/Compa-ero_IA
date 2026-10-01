from app.database import Base
from sqlalchemy import create_engine
sync_engine = create_engine('sqlite:///C:/Users/est.fabianu/AppData/Local/AIWorkmate/database/ai-workmate.db')
Base.metadata.create_all(sync_engine)
print('Sync create_all done')
import sqlite3
conn = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', cursor.fetchall())