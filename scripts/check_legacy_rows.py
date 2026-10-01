import sqlite3
legacy = sqlite3.connect(r'C:\Users\est.fabianu\Documents\Compañero_IA\ai-workmate\backend\data\ai-workmate.db')
cur = legacy.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [t[0] for t in cur.fetchall()]
for t in ['users', 'accounts', 'tasks', 'emails', 'projects']:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    count = cur.fetchone()[0]
    print(f'{t}: {count} rows')
legacy.close()