# geopull

![Main Branch Tests](https://github.com/mansueto-institute/geopull/actions/workflows/build.yml/badge.svg?branch=main)

Simple tool for bulk downloading OSM and GADM geographic files and doing a minimal amount of preprocessing.

## Installation

You can install the package two ways, please make sure to read the section on [dependencies](#dependencies)

Directly from the GitHub repository:

``` bash
pip install git+https://github.com/mansueto-institute/geopull
```

By cloning the repo:

``` bash
git clone https://github.com/mansueto-institute/geopull
pip install -e geopull
```

### Developing

If you'd like to contribute, it's suggested that you install the optional dependencies with the `[dev]` dynamic metadata for setuptools. You can do this by either:

``` bash
pip install "geopull[dev] @ git+https://github.com/mansueto-institute/geopull"
```

By cloning the repo:

``` bash
git clone https://github.com/mansueto-institute/geopull
pip install -e geopull[dev]
```

This will install linters and the requirements for running the tests. For more information as to what is done to the code for testing/linting refer to [GitHub Action](.github/workflows/build.yml).

### Dependencies

This tool depends on [osmium-tool](https://github.com/osmcode/osmium-tool) which you can install with [`conda`](https://anaconda.org/conda-forge/osmium-tool)

## Usage

### Data Directories

When you download data, if you don't tell the program where you'd like to keep the files, it will create a `data/` directory within your current path. This directory will have subdirectories depending on the type of files that will be store in such subdirectory, such as `.pbf` or `.geojson`.
