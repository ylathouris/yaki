
from unittest import mock

import pytest
from pkg_resources import DistributionNotFound


@pytest.fixture()
def mockgetdist():
    with mock.patch("pkg_resources.get_distribution") as mocked:
        yield mocked


@pytest.fixture()
def mockmetadata():
    metadata = {"Author": "Jane Doe", "Author-email": "jane.doe@mail.com"}
    with mock.patch("importlib.metadata.metadata") as mocked:
        mocked.return_value = metadata
        yield mocked
