import hashlib

from dataclasses import dataclass


@dataclass
class User:
    user: str
    password: str | None

    def __post_init__(self):
        self.__password = self.password[:]  # copy the value, but not by reference
        self.password = None
        self.hashed_password = self.__compute_hashed_password()

    def __compute_hashed_password(self):
        return hashlib.sha256(bytes(self.__password, 'utf-8')).hexdigest()

    def get_user(self):
        return self.user

    def get_hashed_password(self):
        return self.hashed_password


