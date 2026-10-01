from app.database import Base
from sqlalchemy import create_engine
import os
tmp = r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.tmp.db'
print('Tmp exists before:', os.path.exists(tmp))
engine = create_engine(f'sqlite:///{tmp}')
print('After create_engine, exists:', os.path.exists(tmp))
Base.metadata.create_all(engine, checkfirst=False)
print('Created')
import sqlite3
conn = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.tmp.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', cursor.fetchall())