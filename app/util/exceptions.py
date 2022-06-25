"""
This file contains the exceptions that are used in the application.
"""


# base class for file errors
class FileError(Exception):
    pass


# error for when there are no ipynb files in the message
class NoNBFileError(FileError):
    pass


# error for when there are too many ipynb files in the message
class TooManyNBsFileError(FileError):
    pass

