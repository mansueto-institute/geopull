"""Country normalizers"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
from geopandas.geodataframe import GeoDataFrame

from geopull.directories import DataDir
from geopull.geofile import DaylightFile, FeatureFile

logger = logging.getLogger(__name__)


@dataclass
class Normalizer(ABC):
    """Abstract class for normalizing a GeoDataFrame."""

    @abstractmethod
    def check(self, ff: FeatureFile) -> bool:
        """Checks if the GeoDataFrame is normalized.

        Usually this is a binary check to test whether the file needs to
        be further normalized.
        """

    @abstractmethod
    def normalize(self, ff: FeatureFile) -> GeoDataFrame:
        """Normalizes the GeoDataFrame."""


@dataclass
class KBlocksNormalizer(Normalizer):
    """A KBlocks normalizer.

    Normalization has to do with the admin levels. If the OSM file has no
    admin_level=4 features, then the file must be normalized. Within this
    context, normalization means removing the maritime boundary and the
    exclusive economic zone from the country polygon. The normalization is
    done using coastline shapefiles from the daylightmap project.
    Additionally all water polygons are removed from the country file.
    """

    datadir: DataDir = field(default=DataDir("."), repr=False)
    _dldf: GeoDataFrame = field(init=False, repr=False)

    @property
    def dldf(self) -> GeoDataFrame:
        """Returns the daylightmap GeoDataFrame.

        If the daylightmap GeoDataFrame has already been loaded into memory,
        then it is returned. Otherwise, it is loaded and then returned.
        """
        if hasattr(self, "_dldf"):
            return self._dldf
        logger.info("Loading daylightmap GeoDataFrame...")
        self._dldf = DaylightFile(datadir=self.datadir).get_water_polygons()
        return self._dldf

    def check(self, ff: FeatureFile) -> bool:
        logger.info("Checking if %s needs to be normalized", ff.country_code)
        gdf = ff.read_file()
        if np.all(gdf["admin_level"] == 4):
            return True
        return False

    def normalize(self, ff: FeatureFile) -> GeoDataFrame:
        logger.info(
            "Checking if %s intersects with daylightmap", ff.country_code
        )
        gdf = ff.read_file()
        intersected = gpd.sjoin(
            left_df=gdf,
            right_df=self.dldf,
            predicate="intersects",
            how="inner",
        )
        if len(intersected) > 0:
            logger.info(
                "Normalizing %s by removing maritime boundary and EEZ",
                ff.country_code,
            )
            gdf = gpd.overlay(
                df1=gdf,
                df2=self.dldf,
                how="difference",
                keep_geom_type=True,
                make_valid=True,
            )

        # logger.info("Removing water features from %s", ff.country_code)
        # waterff = FeatureFile(ff.country_code, "water", datadir=self.datadir)
        # gdf = gpd.overlay(
        #     df1=gdf,
        #     df2=waterff.read_file(),
        #     how="difference",
        #     keep_geom_type=True,
        #     make_valid=True,
        # )
        return gdf

    @staticmethod
    def _get_country_code(gdf: GeoDataFrame) -> str:
        return gdf["iso3"].iloc[0]
