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

from geopull.geofile import PBFFile
from geopull.directories import DataDir

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

        self.args = self.parser.parse_args()

    def main(self) -> None:
        """
        Main method for the geopull package CLI.
        """

        if self.args.subcommand == "download":
            if self.args.source == "osm":
                for country in self.args.country_list:
                    try:
                        pbf_file = PBFFile(
                            country.upper(),
                            datadir=DataDir(self.args.output_dir),
                        )
                        pbf_file.download()
                    except KeyError as e:
                        self.parser.error(str(e))
                    except FileNotFoundError as e:
                        self.parser.error(str(e))
                    except NotADirectoryError as e:
                        self.parser.error(str(e))

    def _build_download_parser(self) -> None:
        self.download_parser.add_argument(
            "source",
            choices={"osm", "gdam"},
            help="Source of the data to download",
            type=str,
        )
        self.download_parser.add_argument(
            "country_list",
            nargs="+",
            help="List of country codes following ISO 3166-1 alpha-3 format",
            type=str,
        )
        self.download_parser.add_argument(
            "--output-dir",
            type=str,
            help=(
                "Output directory for the downloaded files. If not specified, "
                "a data directory will be created in the current working "
                "directory."
            ),
            default=".",
        )


def main() -> None:
    """
    Main driver method for the geopull package CLI.
    """
    cli = GeoPullCLI()
    cli.main()


if __name__ == "__main__":
    main()
