"""Extractor module."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
from geopandas import GeoDataFrame

from geopull.directories import DataDir
from geopull.geofile import PBFFile

logger = logging.getLogger(__name__)


@dataclass
class Extractor(ABC):
    """Abstract class for extracting features from a PBF file."""

    datadir: DataDir = field(repr=False, default=DataDir("."))

    @abstractmethod
    def extract(self, pbf: PBFFile) -> None:
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

    def extract(self, pbf: PBFFile) -> None:
        self._extract_water_features(pbf)
        self._extract_line_string(pbf)
        self._extract_admin_levels(pbf)

    def _extract_admin_levels(self, pbf: PBFFile) -> GeoDataFrame:
        """Extracts admin levels from a PBF file into a parquet file.

        Only the admin levels that are one level higher than 2 for the given
        pbf file are extract. For example if the admin levels on a country are
        {2, 4, 6, 8} then only the admin level 4 features are extracted.

        Args:
            pbf (PBFFile): the PBF file to extract from.

        Returns:
            GeoDataFrame: the extracted admin level features.
        """
        logger.info("Extracting admin levels from %s", pbf.file_name)
        output: Path = pbf.export(
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=["admin_level"],
            geometry_type="polygon",
            overwrite=True,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        gdf["admin_level"] = gdf["admin_level"].astype(int)

        admin_lvls = gdf["admin_level"].unique()
        min_admin_lvl = admin_lvls[admin_lvls > 2].min()

        gdf = gdf[gdf["admin_level"] == min_admin_lvl]
        self._rename_columns(gdf)
        self._gdf_to_parquet(gdf=gdf, fname=pbf.file_name, suffix="admin")
        output.unlink(missing_ok=True)

        return gdf

    def _extract_line_string(self, pbf: PBFFile) -> GeoDataFrame:
        """Extracts line string features from a PBF file.

        These features are needed to create the blocks.

        Args:
            pbf (PBFFile): The PBF file to extract from.

        Returns:
            GeoDataFrame: the extracted line string features.
        """
        logger.info("Extracting line strings from %s", pbf.file_name)
        output: Path = pbf.export(
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
            overwrite=True,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        self._rename_columns(gdf)
        self._gdf_to_parquet(gdf=gdf, fname=pbf.file_name, suffix="linestring")
        output.unlink(missing_ok=True)
        return gdf

    def _extract_water_features(self, pbf: PBFFile) -> GeoDataFrame:
        """Extracts water features from a PBF file.

        These features are needed to create the blocks as well since the
        blocks are should be delineated by water features and not go over them.

        Args:
            pbf (PBFFile): The PBF file to extract from.

        Returns:
            GeoDataFrame: the extracted water features.
        """
        logger.info("Extracting water features from %s", pbf.file_name)
        output: Path = pbf.export(
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
            overwrite=True,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        self._rename_columns(gdf)
        self._gdf_to_parquet(gdf=gdf, fname=pbf.file_name, suffix="water")
        output.unlink(missing_ok=True)
        return gdf

    def _gdf_to_parquet(
        self, gdf: gpd.GeoDataFrame, fname: str, suffix: str = ""
    ) -> None:

        if suffix == "":
            fname = f"{fname}.parquet"
        else:
            fname = f"{fname}-{suffix}.parquet"

        gdf.to_parquet(self.datadir.osm_parquet_dir / fname)

    @staticmethod
    def _rename_columns(gdf: gpd.GeoDataFrame) -> None:
        gdf.columns = gdf.columns.str.replace("@", "")
