"""Country normalizers"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
from geopandas.geodataframe import GeoDataFrame

from geopull.directories import DataDir
from geopull.geofile import DaylightFile


@dataclass
class Normalizer(ABC):
    """Abstract class for normalizing a GeoDataFrame."""

    @abstractmethod
    def check(self, gdf: GeoDataFrame) -> bool:
        """Checks if the GeoDataFrame is normalized.

        Usually this is a binary check to test whether the file needs to
        be further normalized.
        """

    @abstractmethod
    def normalize(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """Normalizes the GeoDataFrame."""


@dataclass
class KBlocksNormalizer(Normalizer):
    """A KBlocks normalizer.

    Normalization has to do with the admin levels. If the OSM file has no
    admin_level=4 features, then the file must be normalized. Within this
    context, normalization means removing the maritime boundary and the
    exclusive economic zone from the country polygon. The normalization is
    done using coastline shapefiles from the daylightmap project.
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
        else:
            self._dldf = DaylightFile(
                datadir=self.datadir
            ).get_water_polygons()
            return self._dldf

    def check(self, gdf: GeoDataFrame) -> bool:
        if np.all(gdf["admin_level"] == 4):
            return True
        return False

    def normalize(self, gdf: GeoDataFrame) -> GeoDataFrame:
        intersected = gpd.sjoin(
            left_df=gdf,
            right_df=self.dldf,
            predicate="intersects",
            how="inner",
        )
        if len(intersected) == 0:
            return gdf
        gdf = gpd.overlay(
            df1=gdf,
            df2=self.dldf,
            how="difference",
            keep_geom_type=True,
            make_valid=True,
        )
        return gdf
