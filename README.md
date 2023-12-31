## Create virtual environment 


```commandline
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Usage
```text
venv\Scripts\python.exe main.py -h

usage: 
    A user (identified with by an email) and password needs to be provided for login, along with an action.

    If you do not have an account, you can register one using -a or --action and specify the action 'register' after that you can choose from the options below.

    Choose an action you want to do.
        - register: Register the user (email) and password
        - view: View all the available events
        - reservation: Make a reservation for a given event
        - cancel: Cancel reservation for a given event
        - info: List the information for your user 
                                     

This is a program that can be used to query information about different events.

options:
      -h, --help            show this help message and exit
      -u USER, --user USER  Specify your email
      -p PASSWORD, --password PASSWORD
                            Specify your password
      -a {register,view,reservation,cancel,info}, --action {register,view,reservation,cancel,info}
                            Choose an action you want to do. - register: Register the user (email) and password - view: View all the available event - reservation: Make a reservation/s for a given event - cancel: Cancel reservation identified by the given barcode - info: List the information for your user
      -e EVENT, --event EVENT
                            Available only for "reservation", it implies that you: - want to make a reservation for -e X event
      -s SEATS, --seats SEATS
                            Available for "reservation", it implies that you: - want to make a reservation of -s N seats
      -b BARCODE, --barcode BARCODE
                            Available for "cancel", it implies that you: - want to make a cancellation for the reservation with barcode -b B

```

## Tables

We have 3 main tables, "users", "events" and "reservation".

The "users" table contains the following columns: "id", "user", "password", "is_admin". The respective type values, in order are: integer, string, string and integer. The primary key is the "id" column.

The "events" table contains the following columns: "id", "name", "date", "price", "seats_available". The respective type values, in order are: integer, string, float, float, integer. The primary key is the "id" column.

The "reservation" table contains the following columns: "user_id", "event_id", "barcode". The respective type values are: integer, integer, integer. The foreign key is structured from the "id" column values from the "users" table and "id" column values from the "events" table.

## Create database environment
```python
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
    
    # drop tables if needed, uncomment the line below
    # drop_tables(db_con=conn, db_cursor=cursor

    # create tables
    create_tables(db_con=conn, db_cursor=cursor)

    # insert events
    insert_events(db_con=conn, db_cursor=cursor)

    cursor.close()
    conn.cursor()
```

## Future improvements

Bulk operations regarding reservations but also cancellations. At the moment we can reserve more seats but for a single event. It would be nice to also have the option to make reservations or cancellations for multiple events at the same time, along with the appropriate number of seats or given barcodes. #   I t - s c h o o l  
 "# It-school" 
#   I t - s c h o o l  
 #   I t - s c h o o l  
 #   I t - s c h o o l  
 