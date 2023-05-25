from unittest.mock import MagicMock, patch

import pytest
from geopandas import GeoDataFrame
from geopull.blocker import (
    Blocker,
    GeoPullBlocker,
    MultiLineString,
    MultiPolygon,
)
from shapely.geometry import LineString, Polygon


@pytest.fixture
def land_df() -> GeoDataFrame:
    gdf = GeoDataFrame(
        {
            "geometry": [
                Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
                Polygon([(0, 0), (0, 2), (2, 2), (2, 0)]),
            ],
        }
    )
    gdf["geometry"] = gdf["geometry"].make_valid()
    return gdf


@pytest.fixture
def line_df() -> GeoDataFrame:
    return GeoDataFrame(
        {
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(0, 0), (1, 1)]),
            ],
            "highway": ["primary", "secondary"],
        }
    )


@pytest.fixture
def blocks_df() -> GeoDataFrame:
    gdf = GeoDataFrame(
        {
            "geometry": [
                Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
                Polygon([(0, 0), (0, 1), (1, 0), (1, 1)]),
                Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)]),
            ]
        }
    )
    gdf["geometry"] = gdf["geometry"].make_valid()
    gdf["code"] = "test"
    return gdf


@pytest.fixture
def blocker(land_df: GeoDataFrame, line_df: GeoDataFrame) -> Blocker:
    return Blocker(region_code="test", land_df=land_df, line_df=line_df)


@pytest.fixture(scope="session")
def land() -> MultiPolygon:
    land = MultiPolygon(
        polygons=[
            Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
            Polygon([(1, 1), (1, 2), (2, 2), (2, 1)]),
            Polygon([(2, 2), (2, 3), (3, 3), (3, 2)]),
        ]
    )
    return land


@pytest.fixture(scope="session")
def line() -> MultiLineString:
    line = MultiLineString(
        lines=[
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)]),
            LineString([(2, 2), (3, 3)]),
        ]
    )
    return line


class TestBlockerInit:
    def test_blocker(self, land_df: GeoDataFrame, line_df: GeoDataFrame):
        blocker = Blocker(region_code="test", land_df=land_df, line_df=line_df)
        assert blocker is not None

    def test_post_init(self, land_df: GeoDataFrame, line_df: GeoDataFrame):
        blocker = Blocker(region_code="test", land_df=land_df, line_df=line_df)
        assert blocker.land_df is not None
        assert blocker.line_df is not None
        assert blocker.region_code == "test"
        assert blocker.land_df.crs == 4326
        assert blocker.line_df.crs == 4326

    def test_post_init_same_crs(
        self, land_df: GeoDataFrame, line_df: GeoDataFrame
    ):
        land_df.crs = 4326
        line_df.crs = 4326
        blocker = Blocker(region_code="test", land_df=land_df, line_df=line_df)
        assert blocker.land_df.crs == 4326
        assert blocker.line_df.crs == 4326


class TestBlockerMethods:
    @patch.object(Blocker, "_make_blocks", MagicMock())
    @patch.object(Blocker, "_validate", MagicMock())
    @patch.object(Blocker, "_add_back_water_features", MagicMock())
    @patch.object(Blocker, "_remove_overlaps", MagicMock())
    @patch.object(Blocker, "_residual_area_check", MagicMock())
    @patch.object(Blocker, "_geohash_blocks", MagicMock())
    def test_build_blocks(self):
        blocker = Blocker(
            region_code="test", land_df=MagicMock(), line_df=MagicMock()
        )
        blocker.build_blocks()
        blocker._make_blocks.assert_called_once()
        blocker._add_back_water_features.assert_called_once()
        assert blocker._validate.call_count == 2
        blocker._remove_overlaps.assert_called_once()
        blocker._residual_area_check.assert_called_once()
        blocker._geohash_blocks.assert_called_once()

    def test_remove_overlaps_no_overlap(self, blocker: Blocker):
        blocks = GeoDataFrame(
            {
                "geometry": [
                    Polygon([(0, 0), (1, 1), (1, 0)]),
                    Polygon([(0, 0), (0, 1), (1, 0), (1, 1)]),
                    # Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)]),
                ]
            }
        )
        blocks = blocks.set_crs(4326)
        blocks = blocker._remove_overlaps(blocks)
        assert blocks.shape[0] == 1

    def test_remove_overlaps(self, blocker: Blocker):
        blocks = GeoDataFrame(
            {
                "geometry": [
                    Polygon([(0, 0), (1, 1), (1, 0)]),
                    Polygon([(0, 0), (0, 1), (1, 0), (1, 1)]),
                    Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)]),
                ]
            }
        )
        blocks = blocks.set_crs(4326)
        blocks = blocker._remove_overlaps(blocks)
        assert blocks.shape[0] == 1

    def test_residual_area_check(
        self, blocker: Blocker, blocks_df: GeoDataFrame
    ):
        blocks_df = blocks_df.set_crs(4326)
        blocks_df = blocker._residual_area_check(blocks_df)
        assert (
            blocks_df.to_crs(3857).area.sum()
            <= blocker.land_df.to_crs(3857).area.sum()
        )

    def test_residual_area_check_no_residue(self, blocker: Blocker):
        blocks_df = GeoDataFrame(
            data={
                "geometry": [
                    Polygon([(10, 20), (10, 20), (20, 20), (20, 10)])
                ],
                "code": ["test"],
            }
        )
        blocks_df = blocks_df.set_crs(4326)
        result = blocker._residual_area_check(blocks_df)
        assert blocks_df.equals(result)

    def test_add_back_water(self, blocker: Blocker):
        blocks_df = GeoDataFrame(
            data={
                "geometry": [
                    Polygon([(10, 20), (10, 20), (20, 20), (20, 10)])
                ],
                "code": ["test"],
            }
        )
        blocks_df = blocks_df.set_crs(4326)
        result = blocker._add_back_water_features(blocks_df)
        assert (
            blocks_df.to_crs(3395).area.sum() > result.to_crs(3395).area.sum()
        )

    def test_add_back_water_no_overlap(
        self, blocker: Blocker, blocks_df: GeoDataFrame
    ):
        blocks_df = blocks_df.set_crs(4326)
        result = blocker._add_back_water_features(blocks_df)
        assert blocks_df.equals(result)

    @patch("geopull.blocker.Blocker._merge_land_lines", MagicMock())
    @patch("geopull.blocker.Blocker._get_land_enclosure", MagicMock())
    @patch("geopull.blocker.Blocker._polygonize", MagicMock())
    @patch("geopull.blocker.GeoDataFrame", MagicMock())
    def test_make_blocks(self, blocker: Blocker):
        blocker._make_blocks()
        blocker._merge_land_lines.assert_called_once()  # type: ignore
        blocker._get_land_enclosure.assert_called_once()  # type: ignore
        blocker._polygonize.assert_called_once()  # type: ignore

    @patch("shapely.union_all", MagicMock())
    @patch("shapely.polygonize", MagicMock())
    @patch("shapely.normalize", MagicMock())
    @patch("shapely.get_parts", MagicMock())
    @patch("shapely.make_valid", MagicMock())
    def test_polygonize(
        self, blocker: Blocker, land: MultiPolygon, line: MultiLineString
    ):
        result = blocker._polygonize(land, line)
        assert result is not None

    def test_validate(self, land_df: GeoDataFrame):
        valid_df = Blocker._validate(land_df)
        assert land_df.equals(valid_df)

    def test_geohash_blocks(self, blocks_df: GeoDataFrame):
        geohashed = Blocker._geohash_blocks(blocks=blocks_df, precision=1)
        assert "block_id" in geohashed.columns
        assert geohashed["block_id"].nunique() > 1

    def test_merge_land_lines(
        self, blocker: Blocker, land: MultiPolygon, line: MultiLineString
    ):
        with (
            patch("shapely.intersection_all") as ia,
            patch("shapely.line_merge") as lm,
        ):
            blocker._merge_land_lines(land, line)
            ia.assert_called_once()
            lm.assert_called_once()

    def test_get_land_enclosure(self, blocker: Blocker, land: MultiPolygon):
        with (
            patch("shapely.get_parts") as cp,
            patch("shapely.get_exterior_ring") as ger,
            patch("shapely.multilinestrings") as mls,
            patch("shapely.line_merge") as lm,
        ):
            blocker._get_land_enclosure(land)
            cp.assert_called_once()
            ger.assert_called_once()
            mls.assert_called_once()
            lm.assert_called_once()


class TestGeoPullBlocker:
    def test_creation_no_args(self):
        with pytest.raises(TypeError):
            GeoPullBlocker()

    @patch("geopull.blocker.ParquetFeatureFile", MagicMock())
    @pytest.mark.parametrize("region_code", ["test", "TEST"])
    def test_creation(self, region_code: str):
        blocker = GeoPullBlocker(region_code=region_code)
        assert blocker is not None
