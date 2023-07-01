import argparse
import logging
import json

from utilities.utils import check_email, check_positive, convert_timestamp
from utilities.logging_util import init_logger
from user.user import User
from database.database import Database

if __name__ == '__main__':
    logger: logging.Logger = init_logger('MAIN LOGGER')
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='''
                                                    This is a program that can be used to query information about different events.\n
                                                ''',
                                     usage='''
    A user (identified with by an email) and password needs to be provided for login, along with an action.\n
    If you do not have an account, you can register one using -a or --action and specify the action 'register' after that you can choose from the options below.\n
    Choose an action you want to do.
        - register: Register the user (email) and password
        - view: View all the available events
        - reservation: Make a reservation for a given event
        - cancel: Cancel reservation for a given event
        - info: List the information for your user 
                                     ''')

    parser.add_argument(
        "-u",
        "--user",
        required=True,
        type=check_email,
        help="Specify your email"
    )

    parser.add_argument(
        "-p",
        "--password",
        required=True,
        help="Specify your password"
    )

    parser.add_argument(
        "-a",
        "--action",
        required=True,
        choices=[
            'register',
            'view',
            'reservation',
            'cancel',
            'info'
        ],
        help='''
            Choose an action you want to do.\n
            - register: Register the user (email) and password \n
            - view: View all the available event \n
            - reservation: Make a reservation/s for a given event \n
            - cancel: Cancel reservation identified by the given barcode \n 
            - info: List the information for your user \n
        '''
    )

    parser.add_argument(
        "-e",
        "--event",
        required=False,
        type=check_positive,
        help='''Available only for "reservation", it implies that you:
             - want to make a reservation for -e X event
             '''
    )

    parser.add_argument(
        "-s",
        "--seats",
        required=False,
        type=check_positive,
        help='''
            Available for "reservation", it implies that you:
            - want to make a reservation of -s N seats
            '''
    )

    parser.add_argument(
        "-b",
        "--barcode",
        required=False,
        type=check_positive,
        help='''
            Available for "cancel", it implies that you:
            - want to make a cancellation for the reservation with barcode -b B
            '''
    )

    # this should contain as keys "user", "password" and "action"
    command_information: dict = vars(parser.parse_args())

    # we will always check first if there is a valid User
    user: User = User(user=command_information['user'], password=command_information['password'])
    database: Database = Database()

    match command_information['action']:
        case 'register':
            query_result: bool = database.register_user(user=user)
            if query_result is True:
                logger.info('Successfully registered!')
                exit(0)
            logger.error('Registration failed!')
            exit(1)
        case 'view':
            if not database.check_user(user=user):
                logger.error('Invalid credentials. Please check that you entered them correctly or make sure you are registered.')
                exit(1)
            query_result: bool | list[dict] = database.view_events()
            match query_result:
                case False:
                    logger.error('Could not list events ...')
                    exit(1)
                case []:
                    logger.info('No events available to display')
                    exit(0)
            logger.info('Events available: ')

            to_display: str = ""
            for event_details in query_result:
                print(event_details)
                id_event, event_information = list(event_details.items())[0]
                to_display += "\n\n\tIdentifier: {}\n\tEvent name: {}\n\tDate: {}\n\tPrice: {} RON\n\tSeats available: {}"\
                    .format(id_event, event_information['name'], convert_timestamp(timestamp=event_information['date']), event_information['price'], event_information['seats_available'])
            logger.info(to_display)
            exit(0)
        case 'reservation':
            if not command_information.get('event'):
                logger.error('An event must be given, -e X or --event X, X being an event id found after querying -a or --action view.')
                exit(1)
            if not database.check_user(user=user):
                logger.error('Invalid credentials. Please check that you entered them correctly or make sure you are registered.')
                exit(1)
            if database.make_reservation(user=user, event=command_information['event'], seats=command_information.get("seats") or 1):
                logger.info('Successfully made a reservation!')
                exit(0)
            logger.error('Could not make the reservation ...')
            exit(1)
        case 'cancel':
            if not command_information.get('barcode'):
                logger.error('No barcode provided')
                exit(1)
            if not database.check_user(user=user):
                logger.error('Invalid credentials. Please check that you entered them correctly or make sure you are registered.')
                exit(1)
            if database.cancel_reservation(user=user, barcode=command_information.get('barcode')):
                logger.info('Successfully made a cancelation!')
                exit(0)
            logger.error('Could not make cancellation ...')
            exit(1)
        case 'info':
            if not database.check_user(user=user):
                logger.error('Invalid credentials. Please check that you entered them correctly or make sure you are registered.')
                exit(1)
            logger.info('User information:')
            user_information: dict = database.get_user_info(user=user)
            print(user_information)
            to_display: str = "\n\tEmail: {}\n\tPassword: {}\n\t".format(user_information['email'], user_information['hashed_password'])
            if isinstance(user_information['reservations'], str):
                to_display += "Reservations: {}".format(user_information['reservations'])
                logger.info(to_display)
                exit(0)
            to_display += "Reservations:\n"
            for reservation in user_information['reservations']:
                to_display += "\t\tEvent name: {}\n\t\tDate: {}\n\t\tBarcode: {}\n\n"\
                    .format(reservation['name'], convert_timestamp(timestamp=reservation['date']), reservation['barcode'])

            logger.info(to_display)
            exit(0)

