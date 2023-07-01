import sqlite3
import json


def create_tables(db_con: sqlite3.Connection, db_cursor: sqlite3.Cursor):
    db_cursor.execute(
        'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(255) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, is_admin INTEGER)'
    )
    db_cursor.execute(
        'CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE, date REAL NOT NULL, price REAL NOT NULL, seats_available INTEGER)'
    )
    db_cursor.execute(
        'CREATE TABLE IF NOT EXISTS reservation (user_id INTEGER, event_id INTEGER, barcode INTEGER UNIQUE, FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (event_id) REFERENCES events(id))'
    )

    db_con.commit()


def insert_events(db_con: sqlite3.Connection, db_cursor: sqlite3.Cursor):
    with open('./spectacole.json') as f:
        events = json.load(f)

    tuple_events = [tuple(event) for event in events]

    db_cursor.executemany(
        "INSERT INTO events (name, date, price, seats_available) VALUES (?, ?, ?, ?)",
        tuple_events
    )

    db_con.commit()


def drop_tables(db_con: sqlite3.Connection, db_cursor: sqlite3.Cursor):
    db_cursor.execute("DROP TABLE users")
    db_cursor.execute("DROP TABLE events")
    db_cursor.execute("DROP TABLE reservation")
    db_con.commit()


if __name__ == '__main__':
    # connect to database
    conn = sqlite3.connect('./database/Spectacole-database.db')
    conn.row_factory = sqlite3.Row  # we would like to return the column names as well, not just the values
    cursor = conn.cursor()

    # create tables
    create_tables(db_con=conn, db_cursor=cursor)

    # insert events
    insert_events(db_con=conn, db_cursor=cursor)

    cursor.close()
    conn.cursor()