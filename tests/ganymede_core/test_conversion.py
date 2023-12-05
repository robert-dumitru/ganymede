import pytest
from pathlib import Path


@pytest.fixture
def simple_test():
    return Path("tests/data/simple_test.ipynb")
