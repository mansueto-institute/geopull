# -*- coding: utf-8 -*-
"""
Created on 2023-01-16 02:52:22-06:00
===============================================================================
@filename:  test_geofile.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   Unit tests for the geopull.geofile module
===============================================================================
"""
# pylint: disable=import-outside-toplevel,missing-function-docstring
# pylint: disable=unused-import, redefined-outer-name, protected-access

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from geopull.geofile import GeoFile, PBFFile, load_country_codes


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
        GeoFile("USA")  # pylint: disable=abstract-class-instantiated


class TestPBFFile:
    """
    Tests the PBFFile class.
    """

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
