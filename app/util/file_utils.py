import telebot


# Indicates that too many ipynb notebooks were passed in the jupyter notebook
class TooManyNBsException(Exception):
    pass


def load_files(documents: telebot.types.Document, path: str = "/tmp") -> None:
    """
    Loads the files from the Telegram message into the local filesystem.

    Args:
        documents:
        path:

    Returns:
    """




def check_files() -> None:
    raise NotImplementedError
