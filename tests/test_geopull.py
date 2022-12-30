# -*- coding: utf-8 -*-
"""
Created on 2022-12-17 07:13:45-05:00
===============================================================================
@filename:  test_geopull.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   Test top-level geopull imoports
===============================================================================
"""
# pylint: disable=import-outside-toplevel,missing-function-docstring
# pylint: disable=unused-import


def test_import_geopull():
    import geopull  # noqa: F401


def test_import_geofile():
    import geopull.geofile  # noqa: F401


def test_import_directories():
    import geopull.directories  # noqa: F401


def test_import_tqdm_download():
    import geopull.tqdm_download  # noqa: F401
