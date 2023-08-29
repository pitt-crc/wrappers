"""Command line applications built by the Pitt Center for Research Computing for wrapping common HPC user tasks."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version('crc-wrappers')

except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = '0.0.0'
