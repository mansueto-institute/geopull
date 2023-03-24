# pylint: disable=import-outside-toplevel,missing-function-docstring,
# pylint: disable=unused-import, protected-access,missing-class-docstring
# pylint: disable=redefined-outer-name

from copy import deepcopy
from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from geopull.geofile import (
    DaylightFile,
    GeoJSONFeatureFile,
)
from geopull.normalizer import GeopullNormalizer, Normalizer


@pytest.fixture
def geodata() -> gpd.GeoDataFrame:
    data = {
        "admin_level": ["2", "2", "4", "4"],
        "geometry": [
            Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
            Polygon([(0, 0), (0, 2), (2, 2), (2, 0)]),
            Polygon([(0, 0), (0, 2), (2, 2), (2, 0)]),
            Polygon([(0, 0), (0, 2), (2, 2), (2, 0)]),
        ],
    }
    gdf = gpd.GeoDataFrame(data=data, crs=4326)
    return gdf


def test_subclass_interface():
    subclasses = Normalizer.__subclasses__()
    for subclass in subclasses:
        assert subclass.__abstractmethods__ == set()


class TestGeopullNormalizer:
    @pytest.fixture
    def normalizer(self):
        return GeopullNormalizer()

    @pytest.fixture
    def geojson(self) -> MagicMock:
        geojson = MagicMock(spec=GeoJSONFeatureFile)
        geojson.country_code = "usa"
        return geojson

    def test_dl(self, normalizer):
        assert isinstance(normalizer.dl, DaylightFile)

    @patch("geopull.normalizer.ParquetFeatureFile", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_admin", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_coastline", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_water", MagicMock())
    def test_normalize(self, normalizer, geojson):
        normalizer.normalize(admin=geojson, water=geojson, linestring=geojson)
        normalizer._normalize_admin.assert_called_once_with(geojson)
        normalizer._normalize_water.assert_called_once()

    @patch("geopull.normalizer.ParquetFeatureFile", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_coastline", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_water", MagicMock())
    @patch.object(GeopullNormalizer, "_normalize_admin", MagicMock())
    def test_normalize_with_coastline(self, normalizer, geojson):
        geojson.gdf = gpd.GeoDataFrame({"admin_level": [2, 2, 2]})
        normalizer.normalize(admin=geojson, water=geojson, linestring=geojson)
        normalizer._normalize_admin.assert_called_once_with(geojson)
        normalizer._normalize_coastline.assert_called_once_with(geojson)
        normalizer._normalize_water.assert_called_once_with(geojson, geojson)

    def test_normalize_admin_keep_two(
        self,
        normalizer: GeopullNormalizer,
        geojson: GeoJSONFeatureFile,
        geodata: gpd.GeoDataFrame,
    ):
        geojson.gdf = geodata.iloc[:3].copy()
        normalizer._normalize_admin(geojson)
        assert geojson.gdf["admin_level"].min() == 2

    def test_normalize_admin_keep_four(
        self,
        normalizer: GeopullNormalizer,
        geojson: GeoJSONFeatureFile,
        geodata: gpd.GeoDataFrame,
    ):
        geojson.gdf = geodata
        normalizer._normalize_admin(geojson)
        assert geojson.gdf["admin_level"].min() == 4

    def test_normalize_admin_no_four(
        self,
        normalizer: GeopullNormalizer,
        geojson: GeoJSONFeatureFile,
        geodata: gpd.GeoDataFrame,
    ):
        geojson.gdf = geodata.iloc[:2].copy()
        normalizer._normalize_admin(geojson)
        assert geojson.gdf["admin_level"].min() == 2

    @pytest.mark.parametrize("intersect", (0, 2))
    @patch.object(GeopullNormalizer, "_get_coastlines", MagicMock())
    @patch("geopandas.sjoin")
    @patch("geopandas.overlay")
    def test_normalize_coastline(
        self, mock_overlay, mock_sjoin, intersect, normalizer, geojson, geodata
    ):
        gdf = gpd.GeoDataFrame({"admin_level": [2, 2, 2]})
        geojson.gdf = gdf
        mock_sjoin.return_value = ["record"] * intersect
        mock_overlay.return_value = geodata
        normalizer._normalize_coastline(geojson)

        if intersect == 0:
            assert geojson.gdf.equals(gdf)
        else:
            geojson.gdf['geometry'] = geojson.gdf.make_valid()
            assert geojson.gdf.equals(geodata)

    @patch("geopandas.overlay")
    def test_normalize_water(
        self,
        mock_overlay: MagicMock,
        normalizer: GeopullNormalizer,
        geojson: GeoJSONFeatureFile,
    ):
        admin = geojson
        water = deepcopy(geojson)
        admin_gdf = MagicMock()
        water_gdf = MagicMock()
        admin.gdf = admin_gdf
        water.gdf = water_gdf

        normalizer._normalize_water(admin, water)
        mock_overlay.assert_called_once_with(
            df1=admin_gdf,
            df2=water_gdf.dissolve(),
            how="difference",
            keep_geom_type=True,
            make_valid=True,
        )

    @patch("geopull.geofile.DaylightFile")
    def test_get_coastlines(
        self,
        mock_dl: MagicMock,
        normalizer: GeopullNormalizer,
        geojson: GeoJSONFeatureFile,
        geodata: gpd.GeoDataFrame,
    ):
        geojson.gdf = geodata
        mock_dl.get_coastline.return_value = "coastlines"
        gdf = normalizer._get_coastlines(admin=geojson, dl=mock_dl)
        mock_dl.get_coastline.assert_called_once_with(
            bbox=(0.0, 0.0, 2.0, 2.0)
        )
        assert gdf == "coastlines"
