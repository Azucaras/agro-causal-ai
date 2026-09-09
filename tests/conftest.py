import warnings

import pytest

warnings.filterwarnings("ignore")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: testes que levam mais de 30s")
