import sqlite3
from settings.settings import DATABASE_PATH, TABLE_ONE, TABLE_TWO 

with sqlite3.connect(DATABASE_PATH) as connection:
    cursor = connection.cursor()

    if not cursor.execute("PRAGMA table_info(%s)" % TABLE_ONE).fetchall():
        cursor.execute("""
           CREATE TABLE %s (  
               id INTEGER PRIMARY KEY,
               trip_id TEXT,
               vehicle_id TEXT,
               direction TEXT,
               route TEXT,
               start_location TEXT,
               end_location TEXT,
               start_time TEXT,
               end_time TEXT,
               duration TEXT
           )
        """ % TABLE_ONE)
        
    if not cursor.execute("PRAGMA table_info(%s)" % TABLE_TWO).fetchall():
        cursor.execute("""
           CREATE TABLE %s (
               id INTEGER PRIMARY KEY,
               datetime TEXT,
               count TEXT,
               direction TEXT,
               route TEXT
           )
        """ % TABLE_TWO)