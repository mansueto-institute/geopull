# pylint: disable=import-outside-toplevel,missing-function-docstring,
# pylint: disable=unused-import, protected-access,missing-class-docstring
# pylint: disable=redefined-outer-name

from unittest.mock import MagicMock, patch

import pytest

from geopull.geofile import PBFFile
from geopull.orchestrator import Orchestrator


class TestOrchestrator:
    @pytest.fixture(scope="function")
    def orchestrator(self):
        return Orchestrator(["usa"])

    def test_countries(self, orchestrator: Orchestrator):
        assert orchestrator.countries == ["usa"]

    def test_pbfs(self, orchestrator: Orchestrator):
        assert len(orchestrator.pbfs) == 1
        assert orchestrator.pbfs[0].country_code == "USA"

    @patch.object(PBFFile, "download", MagicMock())
    def test_download(self, orchestrator: Orchestrator):
        orchestrator.download()
        for pbf in orchestrator.pbfs:
            pbf.download.assert_called_once()

    @patch("geopull.extractor.Extractor")
    def test_extract(self, mock_exc: MagicMock, orchestrator: Orchestrator):
        orchestrator.extract(mock_exc)
        for pbf in orchestrator.pbfs:
            mock_exc.extract.assert_called_once_with(pbf)

    @patch("geopull.normalizer.Normalizer")
    def test_normalize(self, mock_norm: MagicMock, orchestrator: Orchestrator):
        orchestrator.normalize(mock_norm)
        mock_norm.normalize.assert_called_once()

    @pytest.mark.parametrize("ncpu", [None, 4])
    @patch("geopull.orchestrator.Pool")
    def test_pool_mapper(
        self,
        mock_pool: MagicMock,
        ncpu: int | None,
        orchestrator: Orchestrator,
    ):
        def one():
            return 1

        with patch("os.cpu_count", MagicMock(return_value=ncpu)):
            orchestrator._pool_mapper(one, [1, 2, 3])

            if ncpu is None:
                mock_pool.assert_called_once_with(1)
            else:
                mock_pool.assert_called_once_with(ncpu - 1)
