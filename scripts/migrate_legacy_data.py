#!/usr/bin/env python3
"""
Migra datos de la BD legacy (backend/data/ai-workmate.db) a la nueva BD
(%LOCALAPPDATA%/AIWorkmate/database/ai-workmate.db).

Ejecución: python scripts/migrate_legacy_data.py
"""
import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Agregar el directorio backend al path para importar app
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

LEGACY_DB = BACKEND_DIR / "data" / "ai-workmate.db"
NEW_DB_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "AIWorkmate" / "database"
NEW_DB = NEW_DB_DIR / "ai-workmate.db"

# Tablas que NO existen en el nuevo esquema (nuevas o renombradas)
NEW_TABLES = {"sessions", "alembic_version"}

# Tablas legacy que SÍ existen en el nuevo esquema
MIGRATE_TABLES = [
    "users",
    "accounts",
    "audit_logs",
    "embeddings",
    "event_logs",
    "notifications",
    "projects",
    "settings",
    "ai_memory",
    "contacts",
    "email_threads",
    "meetings",
    "emails",
    "followups",
    "tasks",
    "commitments",
    "task_dependencies",
    "teams_channels",
    "teams_chats",
    "teams_messages",
    "onedrive_delta_links",
    "onedrive_files",
    "sharepoint_delta_links",
    "sharepoint_sites",
    "sharepoint_drives",
    "sharepoint_lists",
    "sharepoint_items",
    "sharepoint_list_items",
]


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Obtiene nombres de columnas de una tabla."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def migrate_table(legacy: sqlite3.Connection, new: sqlite3.Connection, table: str):
    """Copia datos de una tabla legacy a la nueva, solo columnas comunes."""
    legacy_cols = get_columns(legacy, table)
    new_cols = get_columns(new, table)
    common_cols = [c for c in legacy_cols if c in new_cols]

    if not common_cols:
        print(f"  WARN {table}: sin columnas comunes, saltando")
        return

    placeholders = ", ".join(["?"] * len(common_cols))
    cols_str = ", ".join(common_cols)

    legacy_cur = legacy.cursor()
    legacy_cur.execute(f"SELECT {cols_str} FROM {table}")
    rows = legacy_cur.fetchall()

    if not rows:
        print(f"  {table}: 0 filas")
        return

    new_cur = new.cursor()
    # Borrar datos existentes en la nueva BD para esa tabla (idempotente)
    new_cur.execute(f"DELETE FROM {table}")
    new_cur.executemany(
        f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})",
        rows,
    )
    new.commit()
    print(f"  {table}: {len(rows)} filas migradas ({len(common_cols)} cols)")


def main():
    if not LEGACY_DB.exists():
        print(f"ERROR BD legacy no encontrada: {LEGACY_DB}")
        return 1

    print(f"Legacy:  {LEGACY_DB}")
    print(f"Nueva:   {NEW_DB}")
    print(f"Inicio:  {datetime.now().isoformat()}")
    print()

    # Borrar BD nueva si existe (para empezar limpio)
    if NEW_DB.exists():
        NEW_DB.unlink()
        print(f"  BD final anterior borrada: {NEW_DB}")

# Usar nombre temporal para evitar problemas de cache/lock
    TEMP_DB = NEW_DB.with_suffix(".tmp.db")
    if TEMP_DB.exists():
        TEMP_DB.unlink()
    print(f"  Usando BD temporal: {TEMP_DB}")
    print(f"  Temporal existe ANTES de imports: {TEMP_DB.exists()}")

    # Importar routers ANTES para registrar modelos
    from app.api.v1 import (
        auth, emails, tasks, projects, ai, notifications, followups,
        health, calendar, commitments, deadlines, search, blockers,
        workmap, connectors, admin, init, installer
    )
    from app.database import Base
    from sqlalchemy import create_engine, MetaData
    import os
    print("  Creando engine...")
    sync_engine = create_engine(f'sqlite:///{TEMP_DB}')
    print(f"  Archivo existe antes de create_all: {TEMP_DB.exists()}")
    if TEMP_DB.exists():
        print(f"  Tamaño archivo: {os.path.getsize(TEMP_DB)}")
    # Usar metadata fresca para evitar cache
    fresh_metadata = MetaData()
    fresh_metadata.reflect(bind=sync_engine)
    print(f"  Tablas reflejadas: {list(fresh_metadata.tables.keys())}")
    Base.metadata.create_all(sync_engine, checkfirst=False)
    print("Tablas creadas en BD temporal")
    sync_engine.dispose()
    print("Engine cerrado")

    # Renombrar temporal a final
    if NEW_DB.exists():
        NEW_DB.unlink()
    TEMP_DB.rename(NEW_DB)
    print(f"BD temporal renombrada a: {NEW_DB}")

    # Backup de la nueva BD por si acaso (después de crear tablas)
    backup = NEW_DB.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(NEW_DB, backup)
    print(f"Backup:  {backup}")
    print()

    # Verificar que las tablas existen
    import sqlite3
    new_check = sqlite3.connect(NEW_DB)
    cur = new_check.cursor()
    cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cur.fetchall()
    print(f"Tablas en nueva BD: {len(tables)}")
    new_check.close()

    # 2. Migrar datos
    legacy = sqlite3.connect(LEGACY_DB)
    legacy.row_factory = sqlite3.Row
    new = sqlite3.connect(NEW_DB)
    new.row_factory = sqlite3.Row

    try:
        print("Iniciando migracion de datos...")
        for table in MIGRATE_TABLES:
            migrate_table(legacy, new, table)

        # Verificar alembic_version
        new_check2 = sqlite3.connect(NEW_DB)
        cur2 = new_check2.cursor()
        cur2.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="alembic_version"')
        if cur2.fetchone():
            cur2.execute("SELECT version_num FROM alembic_version")
            version = cur2.fetchone()
            if version:
                print(f"\nalembic_version actual: {version[0]}")
            else:
                print("\nalembic_version vacia en nueva BD")
        else:
            print("\nTabla alembic_version no existe en nueva BD (normal si no se usaron migraciones)")
        new_check2.close()

        print(f"\nFin: {datetime.now().isoformat()}")
        print("Migracion de esquema completada")
        # NO return aquí - continuar con migración de datos

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        legacy.close()
        new.close()


if __name__ == "__main__":
    exit(main())