"""Generates block geometry for a given country"""

import logging
from dataclasses import dataclass, field

import geopandas as gpd
import shapely
from geopandas import GeoDataFrame
from shapely import MultiLineString, MultiPolygon

from geopull.geofile import ParquetFeatureFile

logger = logging.getLogger(__name__)


@dataclass
class Blocker:
    country_code: str
    land_df: GeoDataFrame = field(init=False, repr=False)
    line_df: GeoDataFrame = field(init=False, repr=False)

    def __post_init__(self):
        if self.country_code.islower():
            self.country_code = self.country_code.upper()
        land_parq = ParquetFeatureFile(
            country_code=self.country_code, features="admin"
        )
        line_parq = ParquetFeatureFile(
            country_code=self.country_code, features="linestring"
        )
        land_df = land_parq.gdf
        land_df = land_df.explode(index_parts=False)
        land_df = land_df[land_df["geometry"].geom_type == "Polygon"]
        self.land_df = land_df

        self.line_df = line_parq.gdf

    def build_blocks(self) -> GeoDataFrame:
        blocks = self._make_blocks()
        blocks = self._validate(blocks)
        blocks = self._add_back_water_features(blocks)
        blocks = self._validate(blocks)
        return blocks

    def _validate(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """Validates the geometry of a GeoDataFrame.

        Args:
            gdf (GeoDataFrame): the GeoDataFrame to validate.

        Returns:
            GeoDataFrame: the validated GeoDataFrame.
        """
        gdf["geometry"] = gdf["geometry"].make_valid()
        gdf = gdf.explode(index_parts=False)
        gdf = gdf[gdf.geom_type == "Polygon"]
        return gdf

    def _add_back_water_features(self, blocks: GeoDataFrame) -> GeoDataFrame:
        """Adds back water features to blocks.

        When the blocks are polygonized, all water cutouts are added back as
        polygons. This function removes those water cutouts from the blocks,
        by overlaying the blocks with the land features, since the land
        features have the water cutouts removed.

        Args:
            blocks (GeoDataFrame): the blocks to add water features back to.

        Returns:
            GeoDataFrame: the blocks with water features added back.
        """
        resid_area = (
            blocks.geometry.to_crs(3395).area.sum()
            - self.land_df.geometry.to_crs(3395).area.sum()
        )
        if resid_area > 0:
            logger.info(
                f"Adding back {resid_area * 0.0001} sq. km of water features."
            )
            blocks = gpd.overlay(
                df1=blocks,
                df2=self.land_df,
                how="intersection",
                keep_geom_type=True,
                make_valid=True,
            )
        return blocks

    def _make_blocks(self) -> GeoDataFrame:
        """A helper function to make blocks from land and line geometries.

        It first converts the land and line geometries to WGS84, then
        it merges the land and line geometries, then it polygonizes the
        union of the land and line geometries. Finally, it returns a
        GeoDataFrame of the polygonized blocks.

        Returns:
            GeoDataFrame: GeoDataFrame of the polygonized blocks.
        """
        linegeo = shapely.set_srid(self.line_df.geometry.to_crs(4326), 4326)
        linegeo = shapely.multilinestrings(linegeo)

        landgeo = shapely.set_srid(self.land_df.geometry.to_crs(4326), 4326)
        landgeo = shapely.multipolygons(landgeo)

        all_lines = self._merge_land_lines(landgeo, linegeo)
        land_enclosure = self._get_land_enclosure(landgeo)
        blocks = self._polygonize(land_enclosure, all_lines)

        gdf = GeoDataFrame(
            data={
                "region_code": self.land_df["iso3"].iloc[0],
                "geometry": blocks,
            },
        ).set_crs(4326)

        return gdf

    def _polygonize(
        self, land: MultiPolygon, line: MultiLineString
    ) -> MultiPolygon:
        """Polygonizes the union of land and line geomtries.

        Args:
            land (MultiPolygon): the MultiPolygon of land.
            line (MultiLineString): the MultiLineString of lines.

        Returns:
            MultiPolygon: the polygonized MultiPolygon.
        """
        logger.info(
            "Polygonizing land and line geometries. for %s", self.country_code
        )
        blocks = shapely.union_all((land, line))
        blocks = shapely.polygonize((blocks,))
        blocks = shapely.get_parts(
            shapely.normalize(shapely.get_parts(blocks))
        )
        blocks = shapely.make_valid(blocks)
        return blocks

    @staticmethod
    def _merge_land_lines(
        land: MultiPolygon, line: MultiLineString
    ) -> MultiLineString:
        """Merges the land and line MultiPolygons.

        Args:
            land (MultiPolygon): the MultiPolygon of land.
            line (MultiLineString): the MultiLineString of lines.

        Returns:
            MultiLineString: the merged MultiLineString.
        """
        line = shapely.intersection_all((line, land))
        line = shapely.line_merge(line)
        return line

    @staticmethod
    def _get_land_enclosure(land: MultiPolygon) -> MultiLineString:
        """Gets the enclosure of a MultiPolygon.

        Args:
            land (MultiPolygon): the MultiPolygon to get the enclosure of.

        Returns:
            MultiLineString: the enclosure of the MultiPolygon.
        """
        parts = shapely.get_parts(land)
        ext_ring = shapely.get_exterior_ring(parts)
        ext_ring = shapely.multilinestrings(ext_ring)
        return shapely.line_merge(ext_ring)
