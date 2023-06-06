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

If you'd like to contribute, it's suggested that you install the optional dependencies with the `[dev]` dynamic metadata for `setuptools`. You can do this by either:

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

### Country Pipeline

The main usage of the package generate blocks from a given OSM country file. The pipeline has four steps:

1. Download a file from [geofabrik](https://www.geofabrik.de/data/download.html). Note: you might also need the `dalightmap`'s [coastlines](https://daylightmap.org/coastlines.html) which you can also download with the CLI.
2. Extract the necessary features for blocking using [`osmium-tool`](#dependencies).
3. Normalize the features using `geopandas`
4. Generate blocks from the normalized features

Each of these is a separate command that can be called via CLI for a set of countries. For example, below you can find how to run the pipeline for countries `DJI`, `SYC`.

#### Downloading

To first download the daylight project's coastline data, you can run:

```bash
geopull download daylight
```

Now you can download the country OSM files:

```bash
geopull download countries DJI SYC
```

#### Extracting

To extract the necessary features from the OSM data, we use `osmium-tool`. You can run this with our CLI as well, using our settings, by running:

```bash
geopull extract DJI SYC
```

#### Normalizing

We normalize some features before we do the blocking. Our normalizer has documentation in the source code if you want to look at it, however for practical purposes you can use the default settings. You can run this by:

```bash
geopull normalize DJI SYC
```

#### Blocking

Finally, you can run the blocking process for the two countries:

```bash
geopull block DJI SYC
```

This will create two `parquet` files that contain the blocks for each country. All files from the process will be located in `./data` by default.

### Using your own data

You can also use our blocking process with two files of your choosing. A [notebook](/docs/examples/own_data.ipynb) example was made that describes this usage.

### Data Directories

When you download data, if you don't tell the program where you'd like to keep the files, it will create a `data/` directory within your current path. This directory will have subdirectories depending on the type of files that will be store in such subdirectory, such as `.pbf` or `.geojson`.
