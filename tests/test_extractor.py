# pylint: disable=import-outside-toplevel,missing-function-docstring,
# pylint: disable=unused-import, protected-access,missing-class-docstring

from unittest.mock import MagicMock, patch

import pytest

from geopull.extractor import Extractor, GeopullExtractor
from geopull.geofile import PBFFile


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

    @patch.object(GeopullExtractor, "_extract_water", MagicMock())
    @patch.object(GeopullExtractor, "_extract_linestring", MagicMock())
    @patch.object(GeopullExtractor, "_extract_admin", MagicMock())
    @patch("geopull.extractor.PBFFile")
    def test_extract(self, pbf, extractor):
        extractor.extract(pbf)
        extractor._extract_water.assert_called_once_with(pbf)
        extractor._extract_linestring.assert_called_once_with(pbf)
        extractor._extract_admin.assert_called_once_with(pbf)

    @patch("geopull.extractor.GeoJSONFeatureFile", MagicMock())
    @patch("geopull.extractor.PBFFile", autospec=True)
    def test_extract_admin(self, pbf: PBFFile, extractor: GeopullExtractor):
        extractor._extract_admin(pbf)
        pbf.export.assert_called_once_with(  # type: ignore
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=["admin_level"],
            geometry_type="polygon",
            overwrite=extractor.overwrite,
            progress=extractor.progress,
            suffix="admin",
        )

    @patch("geopull.extractor.GeoJSONFeatureFile", MagicMock())
    @patch("geopull.extractor.PBFFile", autospec=True)
    def test_extract_linestrings(
        self, pbf: PBFFile, extractor: GeopullExtractor
    ):
        extractor._extract_linestring(pbf)
        pbf.export.assert_called_once_with(  # type: ignore
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=[
                "natural!=coastline,reef",
                "barrier=city_wall,ditch",
                "route",
                "railway",
                "highway!=footway,bridleway,steps,corridor,path,cycleway",
                "waterway",
                (
                    "boundary!=administrative,place,political,postal_code,"
                    "special_economic_zone,user_defined,maritime"
                ),
            ],
            geometry_type="linestring",
            overwrite=extractor.overwrite,
            progress=extractor.progress,
            suffix="linestring",
        )

    @patch("geopull.extractor.GeoJSONFeatureFile", MagicMock())
    @patch("geopull.extractor.PBFFile", autospec=True)
    def test_extract_water(self, pbf: PBFFile, extractor: GeopullExtractor):
        extractor._extract_water(pbf)
        pbf.export.assert_called_once_with(  # type: ignore
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=[
                "natural=water",
                "coastline",
                "strait",
                "bay",
                "hot_spring",
                "shoal",
                "spring",
                "waterway",
                "water",
            ],
            geometry_type="polygon",
            overwrite=extractor.overwrite,
            progress=extractor.progress,
            suffix="water",
        )
