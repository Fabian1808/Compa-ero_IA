import sqlite3
conn = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)
if tables:
    for t in tables:
        cursor.execute(f'PRAGMA table_info({t[0]})')
        cols = cursor.fetchall()
        print(t[0], [c[1] for c in cols])