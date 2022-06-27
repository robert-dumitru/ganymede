"""
This file contains the exceptions that are used in the application.
"""


# base class for file errors
class FileError(Exception):
    pass


# raised when wrong file type is passed
class WrongTypeFileError(FileError):
    pass


# raised when there are no ipynb files in the message
class NoNBFileError(FileError):
    pass


# raised when there are too many ipynb files in the message
class TooManyNBsFileError(FileError):
    pass

