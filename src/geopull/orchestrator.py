"""Orchestration logic for geopull."""
import logging
import os
from dataclasses import dataclass, field
from multiprocessing import Pool
from typing import Callable, Iterable

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from geopull.directories import DataDir
from geopull.extractor import Extractor
from geopull.geofile import GeoJSONFeatureFile, ParquetFeatureFile, PBFFile
from geopull.normalizer import Normalizer

logger = logging.getLogger(__name__)


@dataclass
class Orchestrator:
    """Orchestrates the geopull process."""

    countries: list[str]
    datadir: DataDir = DataDir(".")
    pbfs: list[PBFFile] = field(init=False)

    def __post_init__(self) -> None:
        self.pbfs = [
            PBFFile(country_code=country) for country in self.countries
        ]

    def download(self) -> None:
        """Downloads the OSM files for the given countries."""
        for file in self.pbfs:
            file.download()

    def extract(self, extractor: Extractor) -> None:
        """Extracts features from the OSM files for the given countries.

        Args:
            extractor (Extractor): the extractor to use.
        """
        for file in self.pbfs:
            extractor.extract(file)

    def normalize(self, normalizer: Normalizer) -> None:
        """Normalizes the extracted features.

        Args:
            normalizer (Normalizer): the normalizer to use.
        """
        admin_files = []
        water_files = []
        for country in self.countries:
            admin_files.append(
                GeoJSONFeatureFile(
                    country_code=country,
                    geometry_type="polygon",
                    suffix="admin",
                )
            )
            water_files.append(
                GeoJSONFeatureFile(
                    country_code=country,
                    geometry_type="polygon",
                    suffix="water",
                )
            )

        for country in self.countries:
            admin = GeoJSONFeatureFile(
                country_code=country, geometry_type="polygon", suffix="admin"
            )
            water = GeoJSONFeatureFile(
                country_code=country, geometry_type="polygon", suffix="water"
            )
            linestring = GeoJSONFeatureFile(
                country_code=country,
                geometry_type="linestring",
                suffix="linestring"
            )
            normalizer.normalize(
                admin=admin, water=water, linestring=linestring
            )

    def _pool_mapper(self, func: Callable, iterable: Iterable) -> None:
        ncpu = os.cpu_count()
        if ncpu is None:
            ncpu = 1
        else:
            ncpu -= 1

        with logging_redirect_tqdm():
            with Pool(ncpu) as pool:
                results = tqdm(
                    pool.imap(func, iterable),
                    total=sum(1 for _ in iterable),
                    desc=func.__name__,
                )
                tuple(results)
