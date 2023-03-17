# pylint: disable=import-outside-toplevel,missing-function-docstring,
# pylint: disable=unused-import, protected-access,missing-class-docstring

from unittest.mock import MagicMock, patch

import pytest

from geopull.extractor import Extractor, GeopullExtractor


def test_subclass_interface():
    subclasses = Extractor.__subclasses__()
    for subclass in subclasses:
        assert subclass.__abstractmethods__ == set()


class TestGeopullExtractor:
    @pytest.fixture(scope="class")
    def extractor(self):
        return GeopullExtractor()

    def test_init(self, extractor):
        assert extractor is not None

    @patch.object(GeopullExtractor, "_extract_water_features", MagicMock())
    @patch.object(GeopullExtractor, "_extract_line_string", MagicMock())
    @patch.object(GeopullExtractor, "_extract_admin_levels", MagicMock())
    @patch("geopull.extractor.PBFFile")
    def test_extract(self, pbf, extractor):
        extractor.extract(pbf)
        extractor._extract_water_features.assert_called_once_with(pbf)
        extractor._extract_line_string.assert_called_once_with(pbf)
        extractor._extract_admin_levels.assert_called_once_with(pbf)
