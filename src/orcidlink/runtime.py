#
# Runtime support
#

import os

from orcidlink.lib.config import RuntimeConfig, ServiceConfig
from orcidlink.lib.utils import posix_time_millis


class RuntimeStats:
    start_time: int

    def __init__(self) -> None:
        self.start_time = posix_time_millis()


_config = None


def config() -> RuntimeConfig:
    global _config
    if _config is None:
        _config = ServiceConfig().runtime_config
    return _config


_stats = None


def stats() -> RuntimeStats:
    global _stats
    if _stats is None:
        _stats = RuntimeStats()
    return _stats


def service_path(path: str) -> str:
    return os.path.join(config().service_directory, path)
