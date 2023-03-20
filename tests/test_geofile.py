# pylint: disable=import-outside-toplevel,missing-function-docstring
# pylint: disable=unused-import, redefined-outer-name, protected-access
# pylint: disable=missing-class-docstring, useless-super-delegation

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from geopandas import GeoDataFrame

from geopull.geofile import (
    DaylightFile,
    FeatureFile,
    GeoFile,
    GeoJSONFeatureFile,
    ParquetFeatureFile,
    PBFFile,
    load_country_codes,
)


@pytest.fixture(scope="class")
def pbf_file() -> PBFFile:
    return PBFFile(country_code="USA")


def test_load_country_codes():
    codes = load_country_codes()
    assert isinstance(codes, dict)
    assert len(codes) == 176
    assert "USA" in codes
    assert codes["USA"] == [
        "usa",
        "North America",
        "United States of America",
    ]


def test_geofile_abstract():
    with pytest.raises(TypeError):
        GeoFile()  # pylint: disable=abstract-class-instantiated


class TestPBFFile:
    @staticmethod
    def test_init():
        assert PBFFile(country_code="USA") == PBFFile(country_code="usa")

    @staticmethod
    def test_init_not_valid():
        with pytest.raises(KeyError):
            PBFFile("not_a_country_code")

    @staticmethod
    def test_country_name(pbf_file: PBFFile):
        assert pbf_file.country_name == "usa"

    @staticmethod
    def test_country_code(pbf_file: PBFFile):
        assert pbf_file.country_code == "USA"

    @staticmethod
    def test_continent(pbf_file: PBFFile):
        assert pbf_file.continent == "North America"

    @staticmethod
    def test_proper_name(pbf_file: PBFFile):
        assert pbf_file.proper_name == "United States of America"

    @staticmethod
    def test_filename(pbf_file: PBFFile):
        assert pbf_file.file_name == "usa-latest"

    @staticmethod
    def test_download_url(pbf_file: PBFFile):
        assert (
            pbf_file._download_url
            == "https://download.geofabrik.de/north-america/usa-latest.osm.pbf"
        )

    @staticmethod
    def test_local_path(pbf_file: PBFFile):
        assert (
            pbf_file.local_path
            == Path("data/osm/pbf/usa-latest.osm.pbf").resolve()
        )

    @staticmethod
    def test_geojson_path(pbf_file: PBFFile):
        assert (
            pbf_file.geojson_path
            == Path("data/osm/geojson/usa-latest.geojson").resolve()
        )

    @staticmethod
    def test_download(pbf_file: PBFFile):
        with patch("geopull.geofile.urlretrieve") as mock_retrieve:
            mock_retrieve.return_value = MagicMock()
            mock_retrieve.return_value.status_code = 200
            mock_retrieve.return_value.iter_content.return_value = [b"line1"]
            pbf_file.download()
            mock_retrieve.assert_called_once()

    @staticmethod
    def test_download_overwrite(pbf_file: PBFFile):
        pbf_file.local_path.touch()
        result = pbf_file.download()
        assert result == pbf_file.local_path
        pbf_file.local_path.unlink()

    @staticmethod
    def test_change_path_suffix(pbf_file: PBFFile):
        assert (
            pbf_file._change_path_suffix(pbf_file.local_path, "geojson")
            == Path("data/osm/geojson/usa-latest.osm.geojson").resolve()
        )

    @staticmethod
    def test_build_json_cfg(pbf_file: PBFFile):
        expected = {
            "attributes": {"one": True, "two": True, "three": True},
            "linear_tags": True,
            "area_tags": True,
            "exclude_tags": [],
            "include_tags": ["include", "these', 'tags"],
        }
        assert (
            pbf_file._build_json_config(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
            )
            == expected
        )

    @staticmethod
    def test_export(pbf_file: PBFFile):
        with patch("geopull.geofile.run") as mock_run:
            pbf_file.local_path.touch()
            pbf_file.export(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
            )
            mock_run.assert_called_once()
            pbf_file.local_path.unlink()

    @staticmethod
    def test_export_doesnt_exist(pbf_file: PBFFile):
        with pytest.raises(FileNotFoundError):
            pbf_file.export(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
            )

    @staticmethod
    def test_export_overwrite(pbf_file: PBFFile):
        with patch("geopull.geofile.run"):
            pbf_file.local_path.touch()
            pbf_file.geojson_path.touch()
            pbf_file.export(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
                overwrite=True,
            )
            pbf_file.geojson_path.unlink()
            pbf_file.local_path.unlink()

    @staticmethod
    def test_export_skip_overwrite(pbf_file: PBFFile):
        pbf_file.local_path.touch()
        pbf_file.geojson_path.touch()
        result = pbf_file.export(
            attributes=["one", "two", "three"],
            include_tags=["include", "these', 'tags"],
            overwrite=False,
        )
        assert result == pbf_file.geojson_path
        pbf_file.local_path.unlink()
        pbf_file.geojson_path.unlink()

    @staticmethod
    def test_export_geometry(pbf_file: PBFFile):
        with patch("geopull.geofile.run") as mock_run:
            pbf_file.local_path.touch()
            pbf_file.export(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
                geometry_type="polygon",
            )
            mock_run.assert_called_once()
            pbf_file.local_path.unlink()

    @staticmethod
    def test_export_no_progress(pbf_file: PBFFile):
        with patch("geopull.geofile.run") as mock_run:
            pbf_file.local_path.touch()
            pbf_file.export(
                attributes=["one", "two", "three"],
                include_tags=["include", "these', 'tags"],
                progress=False,
            )
            mock_run.assert_called_once()
            pbf_file.local_path.unlink()

    @staticmethod
    def test_remove_file(pbf_file: PBFFile):
        pbf_file.local_path.touch()
        pbf_file.remove()
        assert not pbf_file.local_path.exists()


class FeatureFileInstance(FeatureFile):
    def read_file(self) -> GeoDataFrame:
        return super().read_file()

    def write_file(self, gdf: GeoDataFrame) -> None:
        return super().write_file(gdf)

    @property
    def local_path(self) -> Path:
        return super().local_path


class TestFeatureFile:
    def test_gdf(self):
        ff = FeatureFileInstance(country_code="USA")
        with patch.object(ff, "read_file") as mock_read:
            mock_read.return_value = "gdf"
            assert ff.gdf == "gdf"
            assert ff.gdf == "gdf"
            ff.gdf = "new_gdf"
            assert ff.gdf == "new_gdf"


class TestParquetFeatureFile:
    @pytest.fixture(scope="class")
    def parquet_file(self):
        return ParquetFeatureFile(country_code="USA", features="admin")

    def test_bad_features(self):
        with pytest.raises(ValueError):
            ParquetFeatureFile(country_code="USA", features="bad")

    def test_features(self, parquet_file: ParquetFeatureFile):
        assert parquet_file.features == "admin"

    def test_local_path(self, parquet_file: ParquetFeatureFile):
        assert (
            parquet_file.local_path
            == Path("data/osm/parquet/usa-latest-admin.parquet").resolve()
        )

    @patch("geopandas.read_parquet")
    def test_read_file(
        self, mock_read: MagicMock, parquet_file: ParquetFeatureFile
    ):
        mock_read.return_value = "gdf"
        assert parquet_file.read_file() == "gdf"
        mock_read.assert_called_once_with(parquet_file.local_path)

    @patch("geopandas.GeoDataFrame")
    def test_write_file(
        self, mock_gdf: MagicMock, parquet_file: ParquetFeatureFile
    ):
        parquet_file.write_file(mock_gdf)
        mock_gdf.to_parquet.assert_called_once_with(parquet_file.local_path)


class TestGeoJSONFeatures:
    @pytest.fixture(scope="class")
    def geojson(self):
        return GeoJSONFeatureFile(
            country_code="USA", geometry_type="polygon", suffix="admin"
        )

    def test_local_path(self, geojson: GeoJSONFeatureFile):
        assert (
            geojson.local_path
            == Path(
                "data/osm/geojson/usa-latest-polygon-admin.geojson"
            ).resolve()
        )

    @patch("geopandas.read_file")
    def test_read_file(
        self, mock_read: MagicMock, geojson: GeoJSONFeatureFile
    ):
        mock_read.return_value = "gdf"
        assert geojson.read_file() == "gdf"
        mock_read.assert_called_once_with(geojson.local_path)

    @patch("geopandas.GeoDataFrame")
    def test_write_file(
        self, mock_gdf: MagicMock, geojson: GeoJSONFeatureFile
    ):
        geojson.write_file(mock_gdf)
        mock_gdf.to_file.assert_called_once_with(
            geojson.local_path, driver="GeoJSON"
        )

    def test_from_path(self):
        path = Path("data/osm/geojson/usa-latest-polygon-admin.geojson")
        geojson = GeoJSONFeatureFile.from_path(path)
        assert geojson.country_code == "USA"
        assert geojson.geometry_type == "polygon"
        assert geojson.suffix == "admin"


class TestDaylightFile:
    @pytest.fixture(scope="function")
    def daylight(self):
        return DaylightFile()

    def test_local_path(self, daylight: DaylightFile):
        assert (
            daylight.local_path
            == Path("data/daylight/coastlines-latest.tar.gz").resolve()
        )

    def test_base_url(self, daylight: DaylightFile):
        assert "daylight-map-distribution" in daylight._base_url

    def test_download_url(self, daylight: DaylightFile):
        assert "daylight-map-distribution" in daylight._download_url

    @patch.object(DaylightFile, "_download_file_url")
    def test_download(self, mock_download: MagicMock, daylight: DaylightFile):
        daylight.download()
        mock_download.assert_called_once_with(overwrite=False)

    @pytest.mark.parametrize("bbox", [None, (0, 0, 1, 1)])
    @patch("geopandas.read_file")
    def test_get_coastline(
        self, mock_read: MagicMock, bbox: tuple | None, daylight: DaylightFile
    ):
        daylight.get_coastline(bbox=bbox)

        if bbox is None:
            mock_read.assert_called_once_with(
                f"tar://{daylight.local_path}!water_polygons.shp"
            )
        else:
            mock_read.assert_called_once_with(
                f"tar://{daylight.local_path}!water_polygons.shp", bbox=bbox
            )
