#!/usr/bin/env python3
"""Convert MariaDB SQL dump to SQLite database.

Parses the mysqldump output and creates a SQLite database with
only the 10 tables needed by the T'ELEFAN MES 4.0 application.

Usage:
    python scripts/convert_to_sqlite.py
    python scripts/convert_to_sqlite.py <dump_path> <output_path>
"""

import os
import re
import sqlite3
import sys

# Tables required by the application (from app/models.py)
REQUIRED_TABLES = {
    'tblfinorder', 'tblfinorderpos', 'tblfinstep',
    'tblmachinereport', 'tblresourceoperation', 'tblresource',
    'tblpartsreport', 'tblbuffer', 'tblbufferpos', 'tblerrorcodes',
}


def clean_create_table(lines: list[str]) -> str:
    """Convert a MySQL CREATE TABLE statement to SQLite-compatible SQL."""
    sql = ' '.join(line.strip() for line in lines)

    # Remove backticks
    sql = sql.replace('`', '')

    # Remove ENGINE=..., CHARSET=..., etc. after closing paren
    sql = re.sub(r'\)\s*ENGINE\s*=.*$', ')', sql)

    # Remove COMMENT 'text' (handle escaped quotes)
    sql = re.sub(r"\s*COMMENT\s+'(?:[^'\\]|\\.)*'", '', sql)

    # Remove AUTO_INCREMENT (column-level and table-level)
    sql = re.sub(r'\s*AUTO_INCREMENT\s*=?\s*\d*', '', sql, flags=re.IGNORECASE)

    # Remove COLLATE
    sql = re.sub(r'\s*COLLATE\s+\S+', '', sql)

    # Remove DEFAULT CHARSET
    sql = re.sub(r'\s*DEFAULT\s+CHARSET\s*=\s*\S+', '', sql, flags=re.IGNORECASE)

    # Convert MySQL data types to SQLite types
    sql = re.sub(r'\bint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\btinyint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bsmallint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bbigint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bmediumint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bvarchar\(\d+\)', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\blongtext\b', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bmediumtext\b', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bdouble\b', 'REAL', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bfloat\b', 'REAL', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bdecimal\(\d+,\d+\)', 'REAL', sql, flags=re.IGNORECASE)
    # datetime stays as-is (SQLite stores as TEXT, SQLAlchemy handles conversion)

    # Remove KEY/INDEX definitions (but keep PRIMARY KEY)
    sql = re.sub(r',\s*(?:UNIQUE\s+)?KEY\s+\w+\s*\([^)]+\)', '', sql)

    # Clean up any double spaces
    sql = re.sub(r'  +', ' ', sql)

    return sql


def clean_insert(sql: str) -> str:
    """Convert a MySQL INSERT statement to SQLite-compatible SQL.

    Handles MySQL backslash string escaping -> SQLite double-quote escaping.
    """
    # Remove backticks
    sql = sql.replace('`', '')

    # Process string escaping: MySQL uses \' for quotes, SQLite uses ''
    result = []
    i = 0
    in_string = False

    while i < len(sql):
        ch = sql[i]

        if not in_string:
            if ch == "'":
                in_string = True
            result.append(ch)
            i += 1
        else:
            # Inside a single-quoted string
            if ch == '\\' and i + 1 < len(sql):
                next_ch = sql[i + 1]
                if next_ch == "'":
                    result.append("''")
                    i += 2
                elif next_ch == '\\':
                    result.append('\\')
                    i += 2
                elif next_ch == 'n':
                    result.append('\n')
                    i += 2
                elif next_ch == 'r':
                    result.append('\r')
                    i += 2
                elif next_ch == '0':
                    result.append('\x00')
                    i += 2
                elif next_ch == 'Z':
                    result.append('\x1a')
                    i += 2
                else:
                    result.append(next_ch)
                    i += 2
            elif ch == "'":
                in_string = False
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1

    return ''.join(result)


def convert(dump_path: str, output_path: str) -> None:
    """Convert a MariaDB dump file to a SQLite database."""
    print(f"  Source : {dump_path}")
    print(f"  Sortie : {output_path}")
    print()

    if os.path.exists(output_path):
        os.remove(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    conn = sqlite3.connect(output_path)
    # Optimisations pour l'import en masse
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA cache_size=100000")

    in_create = False
    create_lines: list[str] = []
    current_table = None
    tables_created = 0
    rows_inserted = 0

    with open(dump_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()

            # Skip empty, comments, MySQL directives
            if not stripped or stripped.startswith('--') or stripped.startswith('/*'):
                continue

            # Skip LOCK/UNLOCK
            if stripped.startswith('LOCK TABLES') or stripped.startswith('UNLOCK TABLES'):
                continue

            # Detect DROP TABLE → track current table
            drop_match = re.match(r'DROP TABLE IF EXISTS `(\w+)`', stripped)
            if drop_match:
                current_table = drop_match.group(1)
                continue

            # Detect CREATE TABLE start
            create_match = re.match(r'CREATE TABLE `(\w+)`', stripped)
            if create_match:
                table_name = create_match.group(1)
                if table_name in REQUIRED_TABLES:
                    in_create = True
                    create_lines = [stripped]
                    current_table = table_name
                else:
                    in_create = False
                continue

            # Accumulate CREATE TABLE lines
            if in_create:
                create_lines.append(stripped)
                # Check end of CREATE TABLE
                if re.match(r'\)\s*ENGINE', stripped) or stripped.rstrip(';') == ')':
                    clean_sql = clean_create_table(create_lines)
                    try:
                        conn.execute(clean_sql)
                        tables_created += 1
                        print(f"  [OK] Table : {current_table}")
                    except Exception as e:
                        print(f"  [ERREUR] Table {current_table}: {e}")
                        print(f"           SQL: {clean_sql[:200]}...")
                    in_create = False
                    create_lines = []
                continue

            # Process INSERT statements
            insert_match = re.match(r'INSERT INTO `(\w+)`', stripped)
            if insert_match:
                table_name = insert_match.group(1)
                if table_name in REQUIRED_TABLES:
                    clean_sql = clean_insert(stripped)
                    try:
                        conn.execute(clean_sql)
                        # Count approximate rows
                        rows = clean_sql.count('),(') + 1
                        rows_inserted += rows
                    except Exception as e:
                        print(f"  [ERREUR] Insert {table_name}: {e}")
                        print(f"           SQL: {stripped[:200]}...")
                continue

    conn.commit()
    conn.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print()
    print(f"  Conversion terminee !")
    print(f"  Tables : {tables_created}")
    print(f"  Lignes : ~{rows_inserted}")
    print(f"  Taille : {size_mb:.1f} MB")


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dump = os.path.join(project_root, 'ressources', 'FestoMES-2025-03-27.sql')
    output = os.path.join(project_root, 'data', 'mes4.db')

    if len(sys.argv) > 1:
        dump = sys.argv[1]
    if len(sys.argv) > 2:
        output = sys.argv[2]

    print()
    print("  ============================================================")
    print("  T'ELEFAN MES 4.0 — Conversion MariaDB -> SQLite")
    print("  ============================================================")
    print()
    convert(dump, output)
