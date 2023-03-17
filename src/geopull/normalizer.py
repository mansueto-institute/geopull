"""Country normalizers"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame

from geopull.directories import DataDir
from geopull.geofile import (
    DaylightFile,
    GeoJSONFeatureFile,
    ParquetFeatureFile,
)

logger = logging.getLogger(__name__)


@dataclass
class Normalizer(ABC):
    """Abstract class for normalizing a GeoDataFrame."""

    @abstractmethod
    def normalize(self, **kwargs) -> GeoDataFrame:
        """Normalizes the GeoDataFrame."""


@dataclass
class GeopullNormalizer(Normalizer):
    """A Geopull normalizer.

    Normalization has to do with the admin levels. If the OSM file has no
    admin_level=4 features, then the file must be normalized. Within this
    context, normalization means removing the maritime boundary and the
    exclusive economic zone from the country polygon. The normalization is
    done using coastline shapefiles from the daylightmap project.
    Additionally all water polygons are removed from the country file.
    """

    datadir: DataDir = field(default=DataDir("."), repr=False)
    _dldf: GeoDataFrame = field(init=False, repr=False)
    dl: DaylightFile = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.dl = DaylightFile(datadir=self.datadir)

    def normalize(self, **kwargs) -> None:
        admin: GeoJSONFeatureFile = kwargs["admin"]
        water: GeoJSONFeatureFile = kwargs["water"]
        linestring: GeoJSONFeatureFile = kwargs["linestring"]

        logger.info(
            "Checking if %s intersects with daylightmap", admin.country_code
        )

        self._normalize_admin(admin)

        if admin.gdf["admin_level"].min() == 2:
            self._normalize_coastline(admin)
        self._normalize_water(admin, water)

        adminp = ParquetFeatureFile(admin.country_code, "admin")
        adminp.write_file(admin.gdf)

        linesp = ParquetFeatureFile(linestring.country_code, "linestring")
        linesp.write_file(linestring.gdf)

    def _normalize_admin(self, admin: GeoJSONFeatureFile):
        gdf: GeoDataFrame = admin.gdf
        gdf["iso3"] = admin.country_code
        gdf = gdf[gdf["admin_level"].str.isnumeric()]
        gdf["admin_level"] = gdf["admin_level"].astype(int)

        admin_lvls = gdf["admin_level"].unique()
        if 4 in admin_lvls:
            gdf.to_crs(epsg=3395, inplace=True)
            gdf["area"] = gdf.area
            admin_areas = gdf.groupby("admin_level")["area"].sum()
            if admin_areas.loc[4] >= admin_areas.loc[2]:
                gdf = gdf[gdf["admin_level"] == 4]
            else:
                gdf = gdf[gdf["admin_level"] == 2]
        else:
            gdf = gdf[gdf["admin_level"] == 2]
        gdf.to_crs(epsg=4326, inplace=True)
        gdf = gdf.dissolve()
        admin.gdf = gdf

    def _normalize_coastline(self, admin: GeoJSONFeatureFile) -> None:
        gdf = admin.gdf
        dldf = self._get_coastlines(admin, self.dl)
        intersected = gpd.sjoin(
            left_df=gdf,
            right_df=dldf,
            predicate="intersects",
            how="inner",
        )
        if len(intersected) > 0:
            logger.info(
                "Normalizing %s by removing maritime boundary and EEZ",
                admin.country_code,
            )
            gdf = gpd.overlay(
                df1=gdf,
                df2=dldf,
                how="difference",
                keep_geom_type=True,
                make_valid=True,
            )
        admin.gdf = gdf

    def _normalize_water(
        self, admin: GeoJSONFeatureFile, water: GeoJSONFeatureFile
    ):
        logger.info("Removing water features from %s", admin.country_code)
        admin_gdf = admin.gdf
        water_gdf = water.gdf
        logger.info("Dissolving water features from %s", admin.country_code)
        water_gdf = water_gdf.dissolve()

        gdf = gpd.overlay(
            df1=admin_gdf,
            df2=water_gdf,
            how="difference",
            keep_geom_type=True,
            make_valid=True,
        )
        admin.gdf = gdf

    def _get_coastlines(
        self, admin: GeoJSONFeatureFile, dl: DaylightFile
    ) -> GeoDataFrame:
        logger.info("Getting coastline for %s", admin.country_code)
        dldf = dl.get_coastline(
            bbox=tuple(*admin.gdf.dissolve().bounds.values)
        )
        return dldf
