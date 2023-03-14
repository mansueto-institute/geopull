"""Orchestration logic for geopull."""
import logging
import os
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Callable, Iterable

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from geopull.directories import DataDir
from geopull.extractor import Extractor
from geopull.geofile import FeatureFile, PBFFile
from geopull.normalizer import Normalizer

logger = logging.getLogger(__name__)


@dataclass
class Orchestrator:
    """Orchestrates the geopull process."""

    countries: list[str]
    datadir: DataDir = DataDir(".")

    def download(self) -> None:
        """Downloads the OSM files for the given countries."""
        files = [PBFFile(country_code=country) for country in self.countries]
        for file in files:
            file.download()

    def extract(self, extractor: Extractor) -> None:
        """Extracts features from the OSM files for the given countries.

        Args:
            extractor (Extractor): the extractor to use.
        """
        files = [PBFFile(country_code=country) for country in self.countries]
        for file in files:
            extractor.extract(file)

    def normalize(self, normalizer: Normalizer) -> None:
        """Normalizes the extracted features.

        Args:
            normalizer (Normalizer): the normalizer to use.
        """
        feature_files = [
            FeatureFile(country_code=country, features="admin")
            for country in self.countries
        ]
        for ff in feature_files:
            if not normalizer.check(ff):
                gdf = normalizer.normalize(ff)
                ff.write_file(gdf)

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
