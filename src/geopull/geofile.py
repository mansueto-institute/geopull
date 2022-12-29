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

    country_code: str
    _country_name: str = field(init=False)
    _continent: str = field(init=False)
    datadir: ClassVar[DataDir] = field(repr=False, default=DataDir("."))

    def __post_init__(self):
        if self.country_code not in COUNTRYMAP:
            raise KeyError(f"{self.country_code} is not a valid country code")
        self._country_name = COUNTRYMAP[self.country_code][0]
        self._continent = COUNTRYMAP[self.country_code][1]

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
        Returns the proper name of the country, i.e. 'benin' -> 'Benin'.

        Returns:
            str: the proper name of the country
        """
        return self.country_name.capitalize()

    @property
    def file_name(self) -> str:
        """
        Returns the file name.

        Returns:
            str: the file name
        """
        return f"{self.country_code.lower()}-latest"

    @abstractmethod
    def download(self) -> Path:
        """
        Downloads the file.
        """


@dataclass
class PBFFile(GeoFile):
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

    def download(self) -> Path:
        local_path = self.datadir.get_pbf_dir().joinpath(
            "".join((self.file_name, ".osm.pbf"))
        )
        if local_path.exists():
            logger.warning(
                "%s already exists, skipping download", local_path.resolve()
            )
            return local_path.resolve()

        with TqdmUpTo(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            miniters=1,
            desc=self._download_url.rsplit("/", maxsplit=1),
        ) as t:
            urlretrieve(
                self._download_url,
                local_path,
                reporthook=t.update_to,
                data=None,
            )
            t.total = t.n

        return local_path.resolve()

    def export(
        self,
        attributes: list[str],
        include_tags: list[str],
        geometry_type: Optional[str] = None,
    ) -> Path:
        """
        Exports the PBF file to the specified path.

        Args:
            attributes (list[str]): list of attributes to export from the PBF
                file.
            include_tags (list[str]): list of tags to include in the export.
            datadir (DataDir): the data directory
            geometry_type (Optional[str], optional): the geometry type to
                export. Defaults to None, in which case al the geometries are
                exported.

        Returns:
            Path: the path to the exported file in the local machine
        """
        source = (
            self.datadir.get_pbf_dir()
            .joinpath(f"{self.file_name}.osm.pbf")
            .resolve()
        )
        if not source.exists():
            raise FileNotFoundError(
                f"{source} does not exist, download it first"
            )

        osmium_args = [
            "osmium",
            "export",
            "-O",  # overwrite existing file
        ]

        if geometry_type is not None:
            osmium_args.append(f"--geometry-type={geometry_type}")
            target = self.datadir.get_geojson_dir().joinpath(
                f"{self.file_name}-{geometry_type}.geojson"
            )
        else:
            target = self.datadir.get_geojson_dir().joinpath(
                f"{self.file_name}.geojson"
            )
        target = target.resolve()

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
