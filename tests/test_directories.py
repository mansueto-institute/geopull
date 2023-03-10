# -*- coding: utf-8 -*-
"""
Created on 2023-01-16 02:40:54-06:00
===============================================================================
@filename:  test_directories.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   Tests the directories module.
===============================================================================
"""
# pylint: disable=import-outside-toplevel,missing-function-docstring
# pylint: disable=unused-import

import pytest

from geopull.directories import DataDir


@pytest.fixture(scope="module")
def datadir(tmp_path) -> DataDir:
    return DataDir(tmp_path)


class TestDataDir:
    """
    Tests the DataDir class.
    """

    @staticmethod
    def test_init(tmp_path):
        data_dir = DataDir(tmp_path)
        assert data_dir.data.exists()
        assert data_dir.data.is_dir()
        assert data_dir.osm_pbf_dir.exists()
        assert data_dir.osm_pbf_dir.is_dir()
        assert data_dir.osm_geojson_dir.exists()
        assert data_dir.osm_geojson_dir.is_dir()

    @staticmethod
    def test_init_not_exists(tmp_path):
        with pytest.raises(FileNotFoundError):
            DataDir(tmp_path.joinpath("not_a_dir"))

    @staticmethod
    def test_init_not_dir(tmp_path):
        with pytest.raises(NotADirectoryError):
            tmp_path.joinpath("not_a_dir").touch()
            DataDir(tmp_path.joinpath("not_a_dir"))
