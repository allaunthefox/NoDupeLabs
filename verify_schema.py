#!/usr/bin/env python3
"""Verify database schema was created correctly."""

import sqlite3

def verify_schema():
    """Verify the database schema."""
    conn = sqlite3.connect('output/index.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    print('Tables:', tables)
    
    # Check files table columns
    cursor.execute('PRAGMA table_info(files)')
    print('\nFiles table columns:')
    for row in cursor.fetchall():
        print(f'  {row[1]} {row[2]}')
    
    # Check if status column exists
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='files'")
    create_sql = cursor.fetchone()[0]
    print(f'\nFiles table CREATE SQL:\n{create_sql}')
    
    conn.close()

if __name__ == '__main__':
    verify_schema()
