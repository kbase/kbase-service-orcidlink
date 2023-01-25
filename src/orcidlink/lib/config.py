import os
import threading
from typing import Optional

import toml
from orcidlink.lib.utils import module_dir
from orcidlink.model import ServiceDescription
from pydantic import BaseModel, Field


class KBaseService(BaseModel):
    url: str = Field(...)


class Auth2Service(KBaseService):
    tokenCacheLifetime: int = Field(...)
    tokenCacheMaxSize: int = Field(...)


class ORCIDLinkService(KBaseService):
    pass


class ORCIDConfig(BaseModel):
    oauthBaseURL: str = Field(...)
    apiBaseURL: str = Field(...)
    clientId: str = Field(...)
    clientSecret: str = Field(...)


class MongoConfig(BaseModel):
    host: str = Field(...)
    port: int = Field(...)
    database: str = Field(...)
    username: str = Field(...)
    password: str = Field(...)


class ModuleConfig(BaseModel):
    serviceRequestTimeout: int = Field(...)


class Services(BaseModel):
    Auth2: Auth2Service
    ORCIDLink: ORCIDLinkService = Field(...)


class UIConfig(BaseModel):
    origin: str = Field(...)


class Config(BaseModel):
    services: Services = Field(...)
    ui: UIConfig = Field(...)
    orcid: ORCIDConfig = Field(...)
    mongo: MongoConfig = Field(...)
    module: ModuleConfig = Field(...)


class GitInfo(BaseModel):
    commit_hash: str = Field(...)
    commit_hash_abbreviated: str = Field(...)
    author_name: str = Field(...)
    author_date: int = Field(...)
    committer_name: str = Field(...)
    committer_date: int = Field(...)
    url: str = Field(...)
    branch: str = Field(...)
    tag: Optional[str] = Field(default=None)


class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.lock = threading.RLock()
        # self.config_data: Optional[Config] = None
        self.config_data = self.get_config_data()

    def get_config_data(self) -> Config:
        with self.lock:
            file_name = self.config_path
            with open(file_name, "r") as in_file:
                config_yaml = toml.load(in_file)
                return Config.parse_obj(config_yaml)

    def config(self, reload: bool = False) -> Config:
        if reload:
            self.config_data = self.get_config_data()

        return self.config_data


GLOBAL_CONFIG_MANAGER = None


def config(reload: bool = False) -> Config:
    global GLOBAL_CONFIG_MANAGER
    if GLOBAL_CONFIG_MANAGER is None:
        GLOBAL_CONFIG_MANAGER = ConfigManager(
            os.path.join(module_dir(), "config/config.toml")
        )
    return GLOBAL_CONFIG_MANAGER.config(reload)


def get_service_description() -> ServiceDescription:
    file_path = os.path.join(module_dir(), "SERVICE_DESCRIPTION.toml")
    with open(file_path, "r") as file:
        return ServiceDescription.parse_obj(toml.load(file))


def get_git_info() -> GitInfo:
    path = os.path.join(module_dir(), "config/git_info.toml")
    with open(path, "r") as fin:
        return GitInfo.parse_obj(toml.load(fin))
