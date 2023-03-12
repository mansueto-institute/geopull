# -*- coding: utf-8 -*-
"""
Created on 2022-12-29 12:37:22-05:00
===============================================================================
@filename:  directories.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   module for ochestration of directory structure
===============================================================================
"""
from pathlib import Path


class DataDir:
    """
    Class for managing the data directory structure of the project.
    """

    def __init__(self, root_path: str) -> None:
        """
        Initializes the DataDir class.

        Args:
            root_path (str): data directory root path

        Raises:
            FileNotFoundError: if the root path does not exist
            NotADirectoryError: if the root path is not a directory
        """
        root = Path(root_path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"directory {root} does not exist")
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a directory")

        data = root.joinpath("data")
        data.mkdir(exist_ok=True)
        data.joinpath("osm").mkdir(exist_ok=True)
        for subdir in ("pbf", "geojson"):
            data.joinpath("osm", subdir).mkdir(exist_ok=True)
        self.data = data

    @property
    def osm_pbf_dir(self) -> Path:
        """
        Returns the path to the PBF files directory.

        Returns:
            Path: path to the PBF files directory.
        """
        pbf_dir = self.data.joinpath("osm", "pbf")
        pbf_dir.mkdir(exist_ok=True)
        return pbf_dir

    @property
    def osm_geojson_dir(self) -> Path:
        """
        Returns the path to the GeoJSON files directory.

        Returns:
            Path: path to the GeoJSON files directory.
        """
        geojson_dir = self.data.joinpath("osm", "geojson")
        geojson_dir.mkdir(exist_ok=True)
        return geojson_dir

    @property
    def osm_parquet_dir(self) -> Path:
        """
        Returns the path to the Parquet files directory.

        Returns:
            Path: path to the Parquet files directory.
        """
        parquet_dir = self.data.joinpath("osm", "parquet")
        parquet_dir.mkdir(exist_ok=True)
        return parquet_dir
