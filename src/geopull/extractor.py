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
    overwrite: bool = False
    progress: bool = False

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

    def _extract_admin_levels(self, pbf: PBFFile) -> None:
        """Extracts admin levels from a PBF file into a parquet file.

        Only the admin levels that are one level higher than 2 for the given
        pbf file are extract. For example if the admin levels on a country are
        {2, 4, 6, 8} then only the admin level 4 features are extracted.

        Args:
            pbf (PBFFile): the PBF file to extract from.
        """
        if (
            self._make_output_path(pbf, "admin").exists()
            and not self.overwrite
        ):
            logger.info("Admin levels already extracted for %s", pbf.file_name)
            return

        logger.info("Extracting admin levels from %s", pbf.file_name)
        output: Path = pbf.export(
            attributes=["type", "id", "version", "changeset", "timestamp"],
            include_tags=["admin_level"],
            geometry_type="polygon",
            overwrite=self.overwrite,
            progress=self.progress,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        gdf = gdf[gdf["admin_level"].str.isnumeric()]
        gdf["admin_level"] = gdf["admin_level"].astype(int)

        admin_lvls = gdf["admin_level"].unique()
        if 4 in admin_lvls:
            gdf = gdf[gdf["admin_level"] == 4]
        else:
            gdf = gdf[gdf["admin_level"] == 2]

        self._rename_columns(gdf)
        gdf = gdf.to_crs(4326)
        gdf.to_parquet(self._make_output_path(pbf, "admin"))
        output.unlink(missing_ok=True)

    def _extract_line_string(self, pbf: PBFFile) -> None:
        """Extracts line string features from a PBF file.

        These features are needed to create the blocks.

        Args:
            pbf (PBFFile): The PBF file to extract from.
        """
        if (
            self._make_output_path(pbf, "linestring").exists()
            and not self.overwrite
        ):
            logger.info("Linestrings already extracted for %s", pbf.file_name)
            return

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
            overwrite=self.overwrite,
            progress=self.progress,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        self._rename_columns(gdf)
        gdf = gdf.to_crs(4326)
        gdf.to_parquet(self._make_output_path(pbf, "linestring"))
        output.unlink(missing_ok=True)

    def _extract_water_features(self, pbf: PBFFile) -> None:
        """Extracts water features from a PBF file.

        These features are needed to create the blocks as well since the
        blocks are should be delineated by water features and not go over them.

        Args:
            pbf (PBFFile): The PBF file to extract from.
        """
        if (
            self._make_output_path(pbf, "water").exists()
            and not self.overwrite
        ):
            logger.info(
                "Water features already extracted for %s", pbf.file_name
            )
            return

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
            overwrite=self.overwrite,
            progress=self.progress,
        )
        gdf: GeoDataFrame = gpd.read_file(output)
        self._rename_columns(gdf)
        gdf = gdf.to_crs(4326)
        gdf.to_parquet(self._make_output_path(pbf, "water"))
        output.unlink(missing_ok=True)

    def _make_output_path(self, pbf: PBFFile, suffix: str = "") -> Path:
        fname = pbf.file_name
        if suffix == "":
            fname = f"{fname}.parquet"
        else:
            fname = f"{fname}-{suffix}.parquet"
        return self.datadir.osm_parquet_dir / fname

    @staticmethod
    def _rename_columns(gdf: gpd.GeoDataFrame) -> None:
        gdf.columns = gdf.columns.str.replace("@", "")
