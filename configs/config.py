import pathlib

DATABASE_STR_PATH: str = "./database/Spectacole-database.db"
DATABASE: pathlib.Path = pathlib.Path(DATABASE_STR_PATH)  # we need a path-like object to feed to sqlite.connect() method
EMAIL_REGEX: str = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
DATE_FORMAT: str = "%Y-%m-%d %H:%M"
