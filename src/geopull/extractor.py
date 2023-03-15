"""Extractor module.

Contains extractor recipes for extracting features from OSM PBF files.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from geopull.directories import DataDir
from geopull.geofile import GeoJSONFeatureFile, PBFFile

logger = logging.getLogger(__name__)


@dataclass
class Extractor(ABC):
    """Abstract class for extracting features from a PBF file."""

    datadir: DataDir = field(repr=False, default=DataDir("."))
    overwrite: bool = False
    progress: bool = False

    @abstractmethod
    def extract(self, pbf: PBFFile) -> list[GeoJSONFeatureFile]:
        """Extracts features from a PBF file.

        This method should be implemented by subclasses and it should contain
        as many extract steps as necessary.

        Args:
            pbf (PBFFile): the PBF file to extract from.
        """


@dataclass
class KBlocksExtractor(Extractor):
    """Extracts features from a PBF file. Useful for saving recipes

    Each extraction pipeline can be an instance of an extractor. In this case
    the only one is used for the kblocks process.

    Attributes:
        datadir (DataDir): the data directory.
    """

    def extract(self, pbf: PBFFile) -> list[GeoJSONFeatureFile]:
        results = []
        results.append(self._extract_water(pbf))
        results.append(self._extract_linestring(pbf))
        results.append(self._extract_admin(pbf))
        return results

    def _extract_admin(self, pbf: PBFFile) -> GeoJSONFeatureFile:
        """Extracts admin levels from a PBF file into a parquet file.

        Only the admin levels that are one level higher than 2 for the given
        pbf file are extract. For example if the admin levels on a country are
        {2, 4, 6, 8} then only the admin level 4 features are extracted.

        Args:
            pbf (PBFFile): the PBF file to extract from.
        """
        return pbf.export(
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=["admin_level"],
            geometry_type="polygon",
            overwrite=self.overwrite,
            progress=self.progress,
            suffix="admin",
        )

        # gdf: GeoDataFrame = gpd.read_file(output)
        # gdf["iso3"] = pbf.country_code
        # gdf = gdf[gdf["admin_level"].str.isnumeric()]
        # gdf["admin_level"] = gdf["admin_level"].astype(int)

        # admin_lvls = gdf["admin_level"].unique()
        # if 4 in admin_lvls:
        #     gdf = gdf[gdf["admin_level"] == 4]
        # else:
        #     gdf = gdf[gdf["admin_level"] == 2]

        # self._rename_columns(gdf)
        # gdf = gdf.to_crs(4326)
        # gdf.to_parquet(self._make_output_path(pbf, "admin"))
        # output.unlink(missing_ok=True)
        # return GeoJSONFeatureFile(country_code=pbf.country_code, features="admin")

    def _extract_linestring(self, pbf: PBFFile) -> GeoJSONFeatureFile:
        """Extracts line string features from a PBF file.

        These features are needed to create the blocks.

        Args:
            pbf (PBFFile): The PBF file to extract from.
        """
        return pbf.export(
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=[
                "natural",
                "barrier",
                "route",
                "railway",
                "highway",
                "waterway",
                "boundary",
            ],
            geometry_type="linestring",
            overwrite=self.overwrite,
            progress=self.progress,
            suffix="linestring",
        )
        # gdf: GeoDataFrame = gpd.read_file(output)
        # self._rename_columns(gdf)
        # gdf = gdf.to_crs(4326)
        # gdf.to_parquet(self._make_output_path(pbf, "linestring"))
        # output.unlink(missing_ok=True)
        # return GeoJSONFeatureFile(
        #     country_code=pbf.country_code, features="linestring"
        # )

    def _extract_water(self, pbf: PBFFile) -> GeoJSONFeatureFile:
        """Extracts water features from a PBF file.

        These features are needed to create the blocks as well since the
        blocks are should be delineated by water features and not go over them.

        Args:
            pbf (PBFFile): The PBF file to extract from.
        """
        return pbf.export(
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=[
                "natural=water",
                "coastline",
                "strait",
                "bay",
                "hot_spring",
                "shoal",
                "spring",
                "waterway",
                "water",
            ],
            geometry_type="polygon",
            overwrite=self.overwrite,
            progress=self.progress,
            suffix="water",
        )
        # gdf: GeoDataFrame = gpd.read_file(output)
        # self._rename_columns(gdf)
        # gdf = gdf.to_crs(4326)
        # gdf.to_parquet(self._make_output_path(pbf, "water"))
        # output.unlink(missing_ok=True)
        # return GeoJSONFeatureFile(country_code=pbf.country_code, features="water")

    # @staticmethod
    # def _rename_columns(gdf: gpd.GeoDataFrame) -> None:
    #     gdf.columns = gdf.columns.str.replace("@", "")
