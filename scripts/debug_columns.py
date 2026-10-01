import sqlite3

legacy = sqlite3.connect(r'C:\Users\est.fabianu\Documents\Compañero_IA\ai-workmate\backend\data\ai-workmate.db')
new = sqlite3.connect(r'C:\Users\est.fabianu\AppData\Local\AIWorkmate\database\ai-workmate.db')

def get_cols(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info({table})')
    return [row[1] for row in cur.fetchall()]

tables = [
    'users', 'accounts', 'audit_logs', 'embeddings', 'event_logs',
    'notifications', 'projects', 'settings', 'ai_memory', 'contacts',
    'email_threads', 'meetings', 'emails', 'followups', 'tasks',
    'commitments', 'task_dependencies', 'teams_channels', 'teams_chats',
    'teams_messages', 'onedrive_delta_links', 'onedrive_files',
    'sharepoint_delta_links', 'sharepoint_sites', 'sharepoint_drives',
    'sharepoint_lists', 'sharepoint_items', 'sharepoint_list_items'
]

for table in tables:
    legacy_cols = get_cols(legacy, table)
    new_cols = get_cols(new, table)
    common = set(legacy_cols) & set(new_cols)
    only_legacy = set(legacy_cols) - set(new_cols)
    only_new = set(new_cols) - set(legacy_cols)
    print(f"\n{table}:")
    print(f"  Legacy ({len(legacy_cols)}): {legacy_cols}")
    print(f"  New ({len(new_cols)}): {new_cols}")
    print(f"  Common ({len(common)}): {sorted(common)}")
    if only_legacy:
        print(f"  Only legacy: {sorted(only_legacy)}")
    if only_new:
        print(f"  Only new: {sorted(only_new)}")

legacy.close()
new.close()