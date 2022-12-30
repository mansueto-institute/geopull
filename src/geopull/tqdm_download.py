# -*- coding: utf-8 -*-
"""
Created on 2022-12-29 04:38:25-05:00
===============================================================================
@filename:  tqdm_download.py
@author:    Manuel Martinez (manmart@uchicago.edu)
@project:   geopull
@purpose:   simple tqdm progress bar to work with urlretrieve for downloading
            files.
===============================================================================
"""

from tqdm import tqdm


class TqdmUpTo(tqdm):
    """
    Provides `update_to(n)` which uses `tqdm.update(delta_n)`.
    """

    def update_to(self, b=1, bsize=1, tsize=None):
        """
        Update the progress bar.

        Args:
            b (int, optional): Number of blocks transferred so far.
                Defaults to 1.
            bsize (int, optional): Size of each block (in tqdm units).
                Defaults to 1.
            tsize (_type_, optional): Total size (in tqdm units). Defaults to
                None. If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        return self.update(b * bsize - self.n)
