# -*- coding: utf-8 -*-
"""
Created on 2022-12-29 04:02:40-05:00
===============================================================================
@filename:  geofile.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   module containing classes that represent geospatial files
===============================================================================
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from importlib.resources import open_text
from pathlib import Path
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Any, ClassVar, Optional
from urllib.request import urlretrieve

import geopandas as gpd
from geopandas import GeoDataFrame

from geopull.directories import DataDir
from geopull.tqdm_download import TqdmUpTo

logger = logging.getLogger(__name__)


def load_country_codes() -> dict[str, list[str]]:
    """
    Loads the country codes from the json file.

    Returns:
        dict[str, list[str]]: dictionary of country codes
    """
    with open_text("geopull", "iso2geofabrik.json") as f:
        return json.load(f)


COUNTRYMAP = load_country_codes()


@dataclass
class GeoFile(ABC):
    """
    Abstract class for representing a geospatial file.

    Args:
        country_code (str): the country code
    """

    datadir: DataDir = field(repr=False, default=DataDir("."))

    @property
    @abstractmethod
    def _base_url(self) -> str:
        """
        Returns the base url for the file.
        """

    @property
    @abstractmethod
    def _download_url(self) -> str:
        """
        Returns the download url.
        """

    @property
    @abstractmethod
    def local_path(self) -> Path:
        """
        Returns the local path.
        """

    @property
    @abstractmethod
    def file_name(self) -> str:
        """
        Returns the file name without the suffix.
        """

    @abstractmethod
    def download(self, overwrite: bool = False) -> Path:
        """
        Downloads the file.

        Args:
            overwrite (bool, optional): Overwrite existing files. Defaults to
                False.

        Returns:
            Path: the path to the downloaded file
        """

    def _download_file_url(self, overwrite: bool = False) -> Path:
        if self.local_path.exists() and not overwrite:
            logger.warning(
                "%s already exists, skipping download", self.local_path
            )
            return self.local_path

        with TqdmUpTo(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            miniters=1,
            desc=self._download_url.rsplit("/", maxsplit=1)[-1],
        ) as t:
            urlretrieve(
                self._download_url,
                self.local_path,
                reporthook=t.update_to,
                data=None,
            )
            t.total = t.n

        return self.local_path


@dataclass
class CountryGeoFile(GeoFile, ABC):
    """GeoFile that corresponds to a single country.

    This should map 1-to-1 with the country files available for download from
    GeoFabrik.

    Attributes:
        country_code (str): the country code
        continent (str): the continent
        proper_name (str): the proper name of the country
        file_name (str): the file name without the suffix
    """

    country_code: str = field(default="")
    _country_name: str = field(init=False)
    _continent: str = field(init=False)

    def __post_init__(self):
        self.country_code = self.country_code.upper()
        if self.country_code not in COUNTRYMAP:
            raise KeyError(f"{self.country_code} is not a valid country code")
        self._country_name = COUNTRYMAP[self.country_code][0]
        self._continent = COUNTRYMAP[self.country_code][1]
        self._proper_name = COUNTRYMAP[self.country_code][2]

    @property
    def country_name(self) -> str:
        """
        Returns the country name.

        Returns:
            str: the country name
        """
        return self._country_name

    @property
    def continent(self) -> str:
        """
        Returns the continent.

        Returns:
            str: the continent
        """
        return self._continent

    @property
    def proper_name(self) -> str:
        """
        Returns the proper name of the country.

        Returns:
            str: the proper name of the country
        """
        return self._proper_name

    @property
    def file_name(self) -> str:
        """
        Returns the file name without the suffix.

        Returns:
            str: the file name
        """
        return f"{self.country_code.lower()}-latest"


@dataclass
class PBFFile(CountryGeoFile):
    """
    Class for representing a PBF file from the Geofabrik server.

    Args:
        country_code (str): the country code

    Returns:
        PBFFile: the PBF file
    """

    _base_url: ClassVar[str] = "https://download.geofabrik.de"

    @property
    def _download_url(self) -> str:
        return "/".join(
            [
                self._base_url,
                self.continent.lower().replace(" ", "-"),
                f"{self.country_name}-latest.osm.pbf",
            ]
        )

    @property
    def local_path(self) -> Path:
        return self.datadir.osm_pbf_dir.joinpath(
            "".join((self.file_name, ".osm.pbf"))
        ).resolve()

    @property
    def geojson_path(self) -> Path:
        """
        Returns the path to the geojson file. Whether the file exists or not.

        Returns:
            Path: the path to the geojson file
        """
        return self.datadir.osm_geojson_dir.joinpath(
            "".join((self.file_name, ".geojson"))
        ).resolve()

    def remove(self) -> None:
        """
        Removes the PBF file from the local directory.
        """
        self.local_path.unlink(missing_ok=True)

    def download(self, overwrite: bool = False) -> Path:
        return self._download_file_url(overwrite=overwrite)

    def export(
        self,
        attributes: list[str],
        include_tags: list[str],
        geometry_type: Optional[str] = None,
        overwrite: bool = False,
        progress: bool = True,
    ) -> Path:
        """
        Exports the PBF file to the specified path as a GeoJSON file.

        Args:
            attributes (list[str]): list of attributes to export from the PBF
                file.
            include_tags (list[str]): list of tags to include in the export.
            datadir (DataDir): the data directory
            geometry_type (Optional[str], optional): the geometry type to
                export. Defaults to None, in which case al the geometries are
                exported.
            overwrite (bool, optional): Overwrite existing files. Defaults to
                False.

        Returns:
            Path: the path to the exported file in the local machine
        """
        logger.info("Exporting (%s, %s)", self.country_code, self.proper_name)
        source = self.datadir.osm_pbf_dir.joinpath(
            f"{self.file_name}.osm.pbf"
        ).resolve()
        if not source.exists():
            raise FileNotFoundError(
                f"{source} does not exist, download it first"
            )

        osmium_args = [
            "osmium",
            "export",
        ]

        if overwrite:
            osmium_args.append("-O")

        if progress:
            osmium_args.append("--progress")
        else:
            osmium_args.append("--no-progress")

        if geometry_type is not None:
            osmium_args.append(f"--geometry-type={geometry_type}")
            target = self.datadir.osm_geojson_dir.joinpath(
                f"{self.file_name}-{geometry_type}.geojson"
            )
        else:
            target = self.datadir.osm_geojson_dir.joinpath(
                f"{self.file_name}.geojson"
            )
        target = target.resolve()
        if target.exists() and not overwrite:
            logger.warning("%s already exists, skipping export", target)
            return target

        osmium_args.extend(["-o", str(target)])

        # not using context manager because it acts weird on Windows
        tmpfile = NamedTemporaryFile(mode="w+", delete=False)
        json.dump(self._build_json_config(attributes, include_tags), tmpfile)
        tmpfile.flush()

        osmium_args.extend(["-c", tmpfile.name])
        osmium_args.append(str(source))

        run(osmium_args, check=True)
        tmpfile.close()
        Path(tmpfile.name).unlink()

        return target

    @staticmethod
    def _change_path_suffix(path: Path, suffix: str) -> Path:
        """
        Changes the suffix of a path.

        Args:
            path (Path): the path
            suffix (str): the new suffix

        Returns:
            Path: the new path
        """
        newpath = Path(path)
        return (
            newpath.parents[1]
            .joinpath(suffix, ".".join((path.stem, suffix)))
            .resolve()
        )

    @staticmethod
    def _build_json_config(
        attributes: list[str], include_tags: list[str]
    ) -> dict[str, Any]:
        """
        Builds the JSON configuration file for the OSM export.

        Args:
            attributes (list[str]): list of attributes to export from the PBF
                file.
            include_tags (list[str]): list of tags to include in the export.

        Returns:
            str: the JSON configuration file
        """
        data: dict[str, Any] = {
            "attributes": {},
            "linear_tags": True,
            "area_tags": True,
            "exclude_tags": [],
            "include_tags": include_tags,
        }
        for attr in attributes:
            data["attributes"][attr] = True

        return data


@dataclass
class DaylightFile(GeoFile):
    """A daylights coastline file"""

    @property
    def local_path(self) -> Path:
        return self.datadir.daylight_dir.joinpath(
            f"{self.file_name}.tar.gz"
        ).resolve()

    @property
    def _base_url(self) -> str:
        return (
            "https://daylight-map-distribution.s3.us-west-1.amazonaws.com"
            "/release/v1.23/coastlines-v1.23.tgz"
        )

    @property
    def _download_url(self) -> str:
        return self._base_url

    @property
    def file_name(self) -> str:
        return "coastlines-latest"

    def download(self, overwrite: bool = False) -> Path:
        return self._download_file_url(overwrite=overwrite)

    def get_water_polygons(self) -> GeoDataFrame:
        """Loads the water polygons from the tar file."""
        return gpd.read_file(f"tar://{self.local_path}!water_polygons.shp")
