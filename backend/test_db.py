import sqlite3
conn = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.db')
print('DB file size:', conn.total_changes)
conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY)')
conn.commit()
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables after manual create:', cursor.fetchall())