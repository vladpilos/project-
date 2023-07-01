import re
import datetime

from argparse import ArgumentTypeError
from configs.config import EMAIL_REGEX, DATE_FORMAT
from random import randint
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF


def check_email(potential_email: str) -> str:
    """
        Function that checks if a given string is a valid email or not based on a regular expression.

        :param potential_email: string value to be checked
        :return: the value if it is a valid email or raises an Exception -> argparse.ArgumentTypeError if not
    """
    if not re.match(EMAIL_REGEX, potential_email):
        raise ArgumentTypeError('{} is not a valid email'.format(potential_email))
    return potential_email


def check_positive(number: str) -> int:
    """
        Function that checks if a string value is a valid integer to be cast to.

        :param number: string that represents a number that can be cast to int or not
        :return: int cast value or raises an Exception -> argparse.ArgumentTypeError if not
    """
    try:
        int_number = int(number)
    except Exception as _:
        raise ArgumentTypeError('{} is not a valid value, cannot be casted to integer.'.format(number))

    if int_number < 1:
        raise ArgumentTypeError('{} must be a positive integer.'.format(number))
    return int_number


def generate_barcodes(number_of_barcodes: int) -> list:
    """
        Generate barcodes
        :param number_of_barcodes: nr of barcodes to generate
        :return: list of barcodes
    """
    barcodes = set()
    while len(barcodes) < number_of_barcodes:
        range_start = 10 ** 7
        range_end = (10 ** 8) - 1
        barcodes.add(randint(range_start, range_end))
    return list(barcodes)


def convert_timestamp(timestamp: float) -> str:
    """
        Convert timestamp to string value date
        :param timestamp: float value, epoch value
        :return: return string value date
    """
    return datetime.datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)


def convert_to_timestamp(date_string: str) -> float:
    """
        Convert string date to timestamp
        :param date_string: date string to convert
        :return: return float value, epoch value
    """
    return datetime.datetime.strptime(date_string, DATE_FORMAT).timestamp()


def generate_pdf(event_name: str, date: float, price: float, barcode: int, email: str):
    """
        Function to generate a pdf with the given fields, event name, date, price, barcode and email

        :param event_name: str value representing the name of the event
        :param date: date in float that will be transformed into a date string later
        :param price: price in float
        :param barcode: barcode generated value
        :param email: email of the user
        :return: None, creates in ./pdf_reservations/ the given pdf below
    """
    canv = canvas.Canvas("./pdf_reservations/{}_{}_{}.pdf".format(barcode, date, email), pagesize=letter)
    canv.setLineWidth(.3)
    canv.setFont('Helvetica', 12)
    canv.drawString(30, 750, 'RESERVATION DOCUMENT')

    canv.drawString(500, 750, "{}".format(convert_timestamp(date)))
    canv.line(480, 747, 580, 747)
    canv.drawString(275, 725, "PRICE:")
    canv.drawString(500, 725, "{}".format(price))
    canv.line(378, 723, 580, 723)

    canv.drawString(30, 703, 'EVENT:')
    canv.line(120, 700, 580, 700)
    canv.drawString(120, 703, "{}".format(event_name))

    canv.drawString(30, 650, 'EMAIL:')
    canv.line(120, 645, 580, 645)
    canv.drawString(120, 650, "{}".format(email))

    barcode_eanbc8 = eanbc.Ean8BarcodeWidget(barcode)
    d = Drawing(50, 10)
    d.add(barcode_eanbc8)
    renderPDF.draw(d, canv, 15, 555)
    canv.save()

