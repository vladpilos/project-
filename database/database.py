import datetime
import sqlite3
import logging

from configs.config import DATABASE
from utilities.logging_util import init_logger
from user.user import User
from utilities.utils import generate_barcodes, generate_pdf


class Database:
    def __init__(self):
        """
            Constructor to initialize the logger, database connection and cursor
        """
        self.logger: logging.Logger = init_logger(type(self).__name__)
        self.database: sqlite3.Connection | None = None
        self.database_cursor: sqlite3.Cursor | None = None
        self.__init_connection()
        self.__init_cursor()

    def __del__(self):
        """
            Destructor -> close connection and cursor
        """
        self.logger.info('Closing database connection and cursor')
        self.database_cursor.close()
        self.database.close()

    def __init_connection(self):
        """
            Private method to initialize connection to the database and explicitly set the query results to be returned
            along with the column names
            :return: None
        """
        self.logger.info('Initialising database connection ...')
        self.database: sqlite3.Connection | None = sqlite3.connect(DATABASE)
        self.database.row_factory = sqlite3.Row  # we would like to return the column names as well, not just the values

    def __init_cursor(self):
        """
            Private method to initialize a cursor from the database connection
            :return: None
        """
        self.logger.info('Initialising cursor ...')
        self.database_cursor: sqlite3.Cursor | None = self.database.cursor()

    def check_user(self, user: User) -> bool:
        """
            Method to check if the user is a valid user in the database or not
            :param user: User object containing the email and hashed password
            :return: True if it is a valid user, False if not or an unexpected error occurs
        """
        try:
            table_user: sqlite3.Cursor = self.database_cursor.execute(
                "SELECT email, password FROM users WHERE email=? AND password=?",
                (user.get_user(), user.get_hashed_password())
            )
            if table_user.fetchone():
                return True
            return False
        except Exception as e:
            self.logger.exception('Unexpected error occurred: {}'.format(str(e)))
            return False

    def get_user_info(self, user: User) -> bool | dict:
        """
            Method used for getting a user information, including reservations made.
            :param user: User object containing information to query the database
            :return: False if information couldn't be queried or dictionary containing information about the user
        """
        table_user: sqlite3.Cursor = self.database_cursor.execute(
            "SELECT id FROM users WHERE email=? AND password=?",
            (user.get_user(), user.get_hashed_password())
        )

        user_information: None | sqlite3.Row = table_user.fetchone()
        if not user_information:
            self.logger.error('Could not find a user with email: {}'.format(user.get_user()))
            return False
        user_id: int = dict(user_information).get('id')
        table_reservation: sqlite3.Cursor = self.database_cursor.execute(
            "SELECT event_id, barcode FROM reservation WHERE user_id=?",
            (user_id,)
        )
        reservations: list[sqlite3.Row] = table_reservation.fetchall()
        view_user_information: dict = {
            'email': user.get_user(),
            'hashed_password': user.get_hashed_password(),
            'reservations': 'There are no reservations for the user.'
        }
        if len(reservations) == 0:
            self.logger.info('No reservations for {}'.format(user.get_user()))
            return view_user_information

        # transform sqlite3.Row to dictionaries
        reservations: list[dict] = [dict(res) for res in reservations]

        # create dictionary for faster later lookup operations
        barcode_event_id_dict: dict = {ev['barcode']: ev['event_id'] for ev in reservations}

        # get all the values from dict (event_id) apply the .join() function to create a valid SQL query
        table_events: sqlite3.Cursor = self.database_cursor.execute(
            "SELECT * FROM events WHERE id IN ({})"
            .format(', '.join('?' for _ in barcode_event_id_dict)),
            list(barcode_event_id_dict.values())
        )

        events_fetched: list[sqlite3.Row] = table_events.fetchall()
        ev_info: dict = {
            dict(ev)['id']: dict(ev) for ev in events_fetched
        }

        view_user_information.update({
            'reservations': [
                {
                    'name': ev_info[barcode_event_id_dict[barcode]]['name'],
                    'date': ev_info[barcode_event_id_dict[barcode]]['date'],
                    'barcode': barcode
                } for barcode in barcode_event_id_dict.keys()
            ]
        })

        return view_user_information

    def register_user(self, user: User) -> bool | str:
        """
            Method used for registering a user in the database
            :param user: User object containing information for registering a user
            :return: False if we couldn't register the user or an error occurred, True if a successful registration was done
        """
        try:
            # check if user already exists with the given email
            self.database_cursor.execute(
                "SELECT email FROM users WHERE email=?",
                (user.get_user(),)
            )
            if self.database_cursor.fetchone():
                self.logger.error('Could not insert user because it already exists.')
                return False
            # insert the user in the database
            self.database_cursor.execute(
                "INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)",
                (user.get_user(), user.get_hashed_password(), 0)
            )
            # commit the registration
            self.database.commit()
            return True
        except Exception as e:
            self.logger.exception('Exception occurred: {}'.format(str(e)))
            return False

    def view_events(self) -> bool | list[dict]:
        """
            Method used for viewing all the events that are available, meaning the date is a future one and number of
            seats are more than 0
            :return: list of dictionaries containing information about events or False if an error occurs
        """
        try:
            # ensure we get available events
            self.database_cursor.execute(
                "SELECT * FROM events WHERE date>? AND seats_available>0",
                (datetime.datetime.now().timestamp(), )
            )
            return [
                {
                    entry['id']: {
                        'name': entry['name'],
                        'date': entry['date'],
                        'price': entry['price'],
                        'seats_available': entry['seats_available']
                    }
                } for entry in [
                    dict(ev) for ev in self.database_cursor.fetchall()
                ]
            ]
        except Exception as e:
            self.logger.exception('Exception occurred: {}'.format(str(e)))
            return False

    def make_reservation(self, user: User, event: int, seats: int = 1):
        """
            Method to make a reservation for a user that provides an event id and a number of seats to reserve.
            If the event has the number of seats available, generate valid barcodes for each reservation and create a
            pdf for each reservation with all the details that are needed. Otherwise, return False because no such reservations
            can be made or an unexpected error occurred.

            :param user: User object with user information
            :param event: event id
            :param seats: number of seats to reserve for a given event
            :return: True and generate PDFs for every reservation or return False if not possible or an unexpected error occurred/
        """
        try:
            # ensure nr of seats is valid
            if seats < 1:
                self.logger.error('Invalid number of seats required.')
                return False

            # check if there is a valid event with the given number of seats available and a valid date
            self.database_cursor.execute(
                "SELECT * FROM events WHERE seats_available>=? AND id=? AND date>?",
                (seats, event, datetime.datetime.now().timestamp())
            )
            result: sqlite3.Row | None = self.database_cursor.fetchone()
            if not result:
                self.logger.info('No reservations can be made now because there are no seats available or events available.')
                return False

            # cast sqlite3.Row to dict
            result: dict = dict(result)

            # get the user id for correlating it with the event id
            self.database_cursor.execute(
                "SELECT id, email FROM users WHERE email=? and password=?",
                (user.get_user(), user.get_hashed_password())
            )
            # we know the user exists, we just directly cast to dict and get the id
            user_information: dict = dict(self.database_cursor.fetchone())
            user_id: int = user_information.get('id')

            while True:
                # generate barcodes and assure there are no other matching barcodes
                barcodes: list = generate_barcodes(number_of_barcodes=seats)
                found_barcodes = self.database_cursor.execute(
                    "SELECT barcode FROM reservation WHERE barcode IN ({})".format(', '.join('?' for _ in range(0, seats))),
                    tuple(barcode for barcode in barcodes)
                )
                if len(found_barcodes.fetchall()) == 0:
                    break

            # make reservations
            self.database_cursor.executemany(
                "INSERT INTO reservation (user_id, event_id, barcode) VALUES (?, ?, ?)",
                [(user_id, event, barcode) for barcode in barcodes]
            )

            # update the events table
            self.database_cursor.execute(
                "UPDATE events SET seats_available=? WHERE id=?",
                (result.get('seats_available') - seats, result.get('id'))
            )

            # commit the changes
            self.database.commit()

            # GENERATE PDFs
            for barcode in barcodes:
                generate_pdf(event_name=result['name'], email=user_information.get('email'), price=result['price'], date=result['date'], barcode=barcode)


            return True
        except Exception as e:
            self.logger.exception('Exception occurred: {}'.format(str(e)))
            return False

    def cancel_reservation(self, user: User, barcode: int) -> bool:
        """
            Method used for canceling a reservation for an event identified by a barcode made.
            If it does not exist a reservation for the user on the given barcode to
            be cancelled, then no action is made. Otherwise, the reservation is cancelled,
            and the tables in the database are updated appropriately.

            :param user: User object representing the user information
            :param barcode: integer value representing the barcode of the reservation that needs to be cancelled
            :return: False if there is nothing to be done or something unexpected happened, True if everything was successful
        """
        try:
            # get the user id to make the correlation between user id and event id from the reservation table
            table_users: sqlite3.Cursor = self.database_cursor.execute(
                "SELECT id FROM users WHERE email=? AND password=?",
                (user.get_user(), user.get_hashed_password())
            )

            # cast to dict, we know the user exists
            user_id: int = dict(table_users.fetchone()).get('id')

            # search if there exists a reservation with the given inputs (user id and event id)
            table_reservation: sqlite3.Cursor = self.database_cursor.execute(
                "SELECT user_id, event_id, barcode FROM reservation WHERE user_id=? AND barcode=?",
                (user_id, barcode)
            )

            reservation: sqlite3.Row | None = table_reservation.fetchone()
            if not reservation:
                self.logger.error('There are no reservation for this user the barcode provided: {}.'.format(barcode))
                return False

            # cast to dict from sqlite3.Row
            reservation: dict = dict(reservation)

            # update reservation table -> DELETE ROW
            self.database_cursor.execute(
                "DELETE FROM reservation WHERE barcode=? AND user_id=? AND event_id=?",
                (barcode, user_id, reservation.get('event_id'))
            )

            # update event table, increment nr of seats available
            self.database.execute(
                "UPDATE events SET seats_available=seats_available + 1 WHERE id=?",
                (reservation.get('event_id'), )
            )

            # commit the changes in db
            self.database.commit()

            return True

        except Exception as e:
            self.logger.exception('Exception occurred: {}'.format(str(e)))
            return False
