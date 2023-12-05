import pytest
from pathlib import Path
import os


@pytest.fixture(scope="session")
def data_path():
    return Path("tests/data")


@pytest.fixture(scope="function", autouse=True)
def environment_setup(data_path):
    # check packages here
    os.environ["JUPYTER_PLATFORM_DIRS"] = "1"
    yield None
    for file in data_path.iterdir():
        if file.suffix not in [".ipynb", ".zip", ".tar"]:
            file.unlink()
