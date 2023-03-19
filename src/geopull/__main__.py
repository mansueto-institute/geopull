# -*- coding: utf-8 -*-
"""
Created on 2022-12-29 08:48:17-05:00
===============================================================================
@filename:  __main__.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   Main entry point for the geopull package CLI
===============================================================================
"""
import logging
from argparse import ArgumentParser

from geopull.directories import DataDir
from geopull.extractor import GeopullExtractor
from geopull.geofile import DaylightFile, PBFFile
from geopull.normalizer import GeopullNormalizer
from geopull.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO)


class GeoPullCLI:
    """
    This class represents a CLI instance for the geopull package.
    """

    def __init__(self) -> None:
        """
        Initializes the GeoPullCLI class.
        """
        self.parser = ArgumentParser(
            description="geopull CLI for downloading OSM/GDAM data",
            prog="geopull",
        )
        subparsers = self.parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands",
            metavar="subcommand",
        )

        self.download_parser = subparsers.add_parser(
            name="download", help="Download OSM/GDAM data"
        )
        self._build_download_parser()

        self.export_parser = subparsers.add_parser(
            name="export", help="Export OSM data from pbfs into geojsons"
        )
        self._build_export_parser()

        self.extract_parser = subparsers.add_parser(
            name="extract",
            help="Extract necessary data from OSM data for blocking.",
        )
        self._build_extract_parser()

        self.normalize_parser = subparsers.add_parser(
            name="normalize",
            help="Normalize extracted data for blocking.",
        )
        self._build_normalize_parser()

        self.args = self.parser.parse_args()

    def main(self) -> None:
        """
        Main method for the geopull package CLI.
        """
        if self.args.subcommand == "download":
            if self.args.filetype == "countries":
                orch = Orchestrator(self.args.country_list)
                try:
                    orch.download()
                except KeyError as e:
                    self.parser.error(str(e))
                except FileNotFoundError as e:
                    self.parser.error(str(e))
                except NotADirectoryError as e:
                    self.parser.error(str(e))
            elif self.args.filetype == "daylight":
                dl = DaylightFile(datadir=DataDir(self.args.output_dir))
                dl.download(self.args.overwrite)
        elif self.args.subcommand == "export":
            for country in self.args.country_list:
                try:
                    pbf_file = PBFFile(
                        country_code=country.upper(),
                        datadir=DataDir(self.args.output_dir),
                    )
                    pbf_file.export(
                        self.args.attributes,
                        self.args.include_tags,
                        self.args.geometry_type,
                        self.args.overwrite,
                    )
                except KeyError as e:
                    self.parser.error(str(e))
                except FileNotFoundError as e:
                    self.parser.error(str(e))
                except NotADirectoryError as e:
                    self.parser.error(str(e))
        elif self.args.subcommand == "extract":
            extractor = GeopullExtractor(
                datadir=DataDir(self.args.output_dir),
                overwrite=self.args.overwrite,
                progress=True,
            )
            orch = Orchestrator(self.args.country_list)
            try:
                orch.extract(extractor=extractor)
            except KeyError as e:
                self.parser.error(str(e))
            except FileNotFoundError as e:
                self.parser.error(str(e))
            except NotADirectoryError as e:
                self.parser.error(str(e))

        elif self.args.subcommand == "normalize":
            normalizer = GeopullNormalizer(
                datadir=DataDir(self.args.output_dir)
            )
            orch = Orchestrator(self.args.country_list)
            orch.normalize(normalizer=normalizer)

        else:
            self.parser.print_usage()

    def _build_download_parser(self) -> None:
        subparsers = self.download_parser.add_subparsers(
            dest="filetype",
            help="Available files types to download",
            metavar="filetype",
        )

        dlparser = subparsers.add_parser(
            "daylight", help="Download daylight data"
        )

        country_parser = subparsers.add_parser(
            "countries", help="Download country data"
        )

        self._add_country_args(country_parser)
        self._add_io_args(dlparser)
        self._add_io_args(country_parser)

    def _build_extract_parser(self) -> None:
        self._add_country_args(self.extract_parser)
        self._add_io_args(self.extract_parser)

    def _build_normalize_parser(self) -> None:
        self._add_country_args(self.normalize_parser)
        self._add_io_args(self.normalize_parser)

    def _build_export_parser(self) -> None:
        self.export_parser.add_argument(
            "--attributes",
            type=str,
            nargs="+",
            help="List of attributes to export",
            default=[],
        )
        self.export_parser.add_argument(
            "--include-tags",
            type=str,
            nargs="+",
            help="List of tags to include; same as osmium-tool.",
            default=[],
        )
        self.export_parser.add_argument(
            "--geometry-type",
            type=str,
            choices={"point", "linestring", "polygon"},
            default=None,
            help="Geometry type to export",
        )
        self._add_country_args(self.export_parser)
        self._add_io_args(self.export_parser)

    def _add_io_args(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--output-dir",
            "-o",
            type=str,
            help=(
                "Output directory for the downloaded files. If not specified, "
                "a data directory will be created in the current working "
                "directory."
            ),
            default=".",
        )
        parser.add_argument(
            "--overwrite",
            "-O",
            action="store_true",
            help="Overwrite existing files",
            default=False,
        )

    def _add_country_args(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "country_list",
            metavar="country-list",
            nargs="+",
            help=(
                "Space-delimited list of country codes following ISO 3166-1 "
                "alpha-3 format"
            ),
            type=str,
        )


def main() -> None:
    """
    Main driver method for the geopull package CLI.
    """
    cli = GeoPullCLI()
    cli.main()


if __name__ == "__main__":
    main()
