"""
Configuration support for this service

A KBase service requires at least a minimal, and often substantial, configuration in
order to operate. Some configuration, like the base url for services, differs between
each KBase environment. Other configuration represents information that may change over
time, such as urls. Sill other configuration data contains private information like
credentials, which must be well controlled.

Because configuration is needed throughout the service's code, it is provided by means
of a module variable which is populated when the module is first loaded.
"""

import json
import os
import tomllib
from typing import Optional
from urllib.parse import urljoin, urlparse

from pydantic import Field

from orcidlink.lib.type import ServiceBaseModel
from orcidlink.model import ServiceDescription


class GitInfo(ServiceBaseModel):
    commit_hash: str = Field(...)
    commit_hash_abbreviated: str = Field(...)
    author_name: str = Field(...)
    author_date: int = Field(...)
    committer_name: str = Field(...)
    committer_date: int = Field(...)
    url: str = Field(...)
    branch: str = Field(...)
    tag: Optional[str] = Field(default=None)


class ServiceDefault(ServiceBaseModel):
    path: str = Field(...)
    env_name: str = Field(...)


class ServiceDefaults(ServiceBaseModel):
    auth2: ServiceDefault = Field(...)
    orcid_link: ServiceDefault = Field(...)


SERVICE_DEFAULTS = ServiceDefaults(
    auth2=ServiceDefault(path="auth", env_name="KBASE_SERVICE_AUTH"),
    orcid_link=ServiceDefault(path="orcidlink", env_name="KBASE_SERVICE_ORCID_LINK"),
)


class IntEnvironmentVariable(ServiceBaseModel):
    value: Optional[int] = Field(default=None)
    unit: str = Field(...)
    required: bool = Field(...)
    env_name: str = Field(...)
    description: str = Field(...)


class IntEnvironmentVariables(ServiceBaseModel):
    token_cache_lifetime: IntEnvironmentVariable = Field(...)
    token_cache_max_items: IntEnvironmentVariable = Field(...)
    request_timeout: IntEnvironmentVariable = Field(...)
    mongo_port: IntEnvironmentVariable = Field(...)
    linking_session_lifetime: IntEnvironmentVariable = Field(...)
    orcid_authorization_retirement_age: IntEnvironmentVariable = Field(...)


INT_CONSTANT_DEFAULTS = IntEnvironmentVariables(
    token_cache_lifetime=IntEnvironmentVariable(
        value=300,
        unit="second",
        required=True,
        env_name="TOKEN_CACHE_LIFETIME",
        description=(
            "The duration, in seconds, for which KBase Auth Service tokens "
            "may be cached."
        ),
    ),
    token_cache_max_items=IntEnvironmentVariable(
        value=20000,
        unit="items",
        required=True,
        env_name="TOKEN_CACHE_MAX_ITEMS",
        description=(
            "The number of KBase Auth tokens which may be cached at one time. "
            "The caching strategy determines behavior when the cache is full."
        ),
    ),
    request_timeout=IntEnvironmentVariable(
        value=60,
        unit="second",
        required=True,
        env_name="REQUEST_TIMEOUT",
        description=(""),
    ),
    mongo_port=IntEnvironmentVariable(
        required=True, unit="port", env_name="MONGO_PORT", description=("")
    ),
    linking_session_lifetime=IntEnvironmentVariable(
        required=True,
        env_name="LINKING_SESSION_LIFETIME",
        value=600,
        unit="second",
        description=(""),
    ),
    orcid_authorization_retirement_age=IntEnvironmentVariable(
        required=True,
        env_name="ORCID_AUTHORIZATION_RETIREMENT_AGE",
        value=1_209_600,
        unit="second",
        description=(""),
    ),
)


# String constants


class StrEnvironmentVariable(ServiceBaseModel):
    value: Optional[str] = Field(default=None)
    required: bool = Field(...)
    env_name: str = Field(...)
    description: str = Field(...)


class StrEnvironmentVariables(ServiceBaseModel):
    service_directory: StrEnvironmentVariable = Field(...)
    kbase_endpoint: StrEnvironmentVariable = Field(...)
    orcid_api_base_url: StrEnvironmentVariable = Field(...)
    orcid_oauth_base_url: StrEnvironmentVariable = Field(...)
    orcid_site_base_url: StrEnvironmentVariable = Field(...)
    orcid_client_id: StrEnvironmentVariable = Field(...)
    orcid_client_secret: StrEnvironmentVariable = Field(...)
    manager_role: StrEnvironmentVariable = Field(...)
    mongo_host: StrEnvironmentVariable = Field(...)
    mongo_database: StrEnvironmentVariable = Field(...)
    mongo_username: StrEnvironmentVariable = Field(...)
    mongo_password: StrEnvironmentVariable = Field(...)
    orcid_scopes: StrEnvironmentVariable = Field(...)
    log_level: StrEnvironmentVariable = Field(...)
    linking_session_return_url: StrEnvironmentVariable = Field(...)


STR_ENVIRONMENT_VARIABLE_DEFAULTS = StrEnvironmentVariables(
    service_directory=StrEnvironmentVariable(
        required=True,
        env_name="SERVICE_DIRECTORY",
        value="/kb/module",
        description=("The directory in which the service is installed"),
    ),
    kbase_endpoint=StrEnvironmentVariable(
        required=True, env_name="KBASE_ENDPOINT", description=("")
    ),
    orcid_api_base_url=StrEnvironmentVariable(
        required=True, env_name="ORCID_API_BASE_URL", description=("")
    ),
    orcid_oauth_base_url=StrEnvironmentVariable(
        required=True, env_name="ORCID_OAUTH_BASE_URL", description=("")
    ),
    orcid_site_base_url=StrEnvironmentVariable(
        required=True, env_name="ORCID_SITE_BASE_URL", description=("")
    ),
    orcid_client_id=StrEnvironmentVariable(
        required=True, env_name="ORCID_CLIENT_ID", description=("")
    ),
    orcid_client_secret=StrEnvironmentVariable(
        required=True, env_name="ORCID_CLIENT_SECRET", description=("")
    ),
    orcid_scopes=StrEnvironmentVariable(
        required=True,
        env_name="ORCID_SCOPES",
        value="/read-limited /activities/update",
        description=(""),
    ),
    manager_role=StrEnvironmentVariable(
        required=True,
        env_name="MANAGER_ROLE",
        value="ORCIDLINK_MANAGER",
        description=(""),
    ),
    mongo_host=StrEnvironmentVariable(
        required=True, env_name="MONGO_HOST", description=("")
    ),
    mongo_database=StrEnvironmentVariable(
        required=True, env_name="MONGO_DATABASE", description=("")
    ),
    mongo_username=StrEnvironmentVariable(
        required=True, env_name="MONGO_USERNAME", description=("")
    ),
    mongo_password=StrEnvironmentVariable(
        required=True, env_name="MONGO_PASSWORD", description=("")
    ),
    log_level=StrEnvironmentVariable(
        required=True, env_name="LOG_LEVEL", value="INFO", description=("")
    ),
    linking_session_return_url=StrEnvironmentVariable(
        required=True, env_name="LINKING_SESSION_RETURN_URL", description=("")
    )
)


class RuntimeConfig(ServiceBaseModel):
    service_directory: str = Field(...)
    kbase_endpoint: str = Field(...)
    request_timeout: int = Field(...)
    token_cache_lifetime: int = Field(...)
    token_cache_max_items: int = Field(...)
    log_level: str = Field(...)
    manager_role: str = Field(...)

    orcid_api_base_url: str = Field(...)
    orcid_oauth_base_url: str = Field(...)
    orcid_site_base_url: str = Field(...)
    orcid_client_id: str = Field(...)
    orcid_client_secret: str = Field(...)
    orcid_scopes: str = Field(...)
    orcid_authorization_retirement_age: int = Field(...)

    linking_session_lifetime: int = Field(...)
    linking_session_return_url: str = Field(...)

    mongo_host: str = Field(...)
    mongo_port: int = Field(...)
    mongo_database: str = Field(...)
    mongo_username: str = Field(...)
    mongo_password: str = Field(...)

    ui_origin: str = Field(...)

    auth_url: str = Field(...)
    orcidlink_url: str = Field(...)


class ServiceConfig:
    kbase_endpoint: str
    runtime_config: RuntimeConfig

    def __init__(self) -> None:
        self.kbase_endpoint = self.get_str_environment_variable(
            STR_ENVIRONMENT_VARIABLE_DEFAULTS.kbase_endpoint
        )
        self.runtime_config = RuntimeConfig(
            service_directory=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.service_directory
            ),
            kbase_endpoint=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.kbase_endpoint
            ),
            request_timeout=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.request_timeout
            ),
            token_cache_lifetime=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.token_cache_lifetime
            ),
            token_cache_max_items=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.token_cache_max_items
            ),
            orcid_authorization_retirement_age=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.orcid_authorization_retirement_age
            ),
            log_level=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.log_level
            ),
            manager_role=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.manager_role
            ),
            orcid_api_base_url=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_api_base_url
            ),
            orcid_oauth_base_url=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_oauth_base_url
            ),
            orcid_site_base_url=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_site_base_url
            ),
            orcid_client_id=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_client_id
            ),
            orcid_client_secret=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_client_secret
            ),
            orcid_scopes=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.orcid_scopes
            ),
            linking_session_lifetime=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.linking_session_lifetime
            ),
            linking_session_return_url=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.linking_session_return_url
            ),
            mongo_host=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.mongo_host
            ),
            mongo_port=self.get_int_environment_variable(
                INT_CONSTANT_DEFAULTS.mongo_port
            ),
            mongo_database=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.mongo_database
            ),
            mongo_username=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.mongo_username
            ),
            mongo_password=self.get_str_environment_variable(
                STR_ENVIRONMENT_VARIABLE_DEFAULTS.mongo_password
            ),
            ui_origin=self.get_ui_origin(),
            auth_url=self.get_service_url(SERVICE_DEFAULTS.auth2),
            orcidlink_url=self.get_own_url(SERVICE_DEFAULTS.orcid_link),
        )

    def get_service_url(self, service_default: ServiceDefault) -> str:
        env_path = os.environ.get(service_default.env_name)
        path = env_path or service_default.path

        # Note that urljoin ignores (strips off) any trailing forward slashes
        # from kbase_endpoint
        return urljoin(self.kbase_endpoint, path)

    def get_own_url(self, service_default: ServiceDefault) -> str:
        env_path = os.environ.get(service_default.env_name)
        path = env_path or service_default.path
        # Note that urljoin ignores (strips off) any trailing forward slashes
        # from kbase_endpoint
        return urljoin(self.kbase_endpoint, path)

    # Integer environment variables
    @staticmethod
    def get_int_environment_variable(
        environment_variable: IntEnvironmentVariable,
    ) -> int:
        value = os.environ.get(environment_variable.env_name)

        if value is not None:
            return int(value)

        if environment_variable.value is not None:
            return environment_variable.value

        raise ValueError(
            f'The environment variable "{environment_variable.env_name}" is missing '
            "and there is no default value"
        )

    # String environment variables
    @staticmethod
    def get_str_environment_variable(
        environment_variable: StrEnvironmentVariable,
    ) -> str:
        value = os.environ.get(environment_variable.env_name)

        if value is not None:
            return value

        if environment_variable.value is not None:
            return environment_variable.value

        raise ValueError(
            f'The environment variable "{environment_variable.env_name}" is missing'
            " and there is no default value"
        )

    # misc

    def get_ui_origin(self) -> str:
        """
        Returns the "origin" suitable for usage in urls targeting a KBase user interface
        in the current KBase deployment environment.

        The deployment environment is indicated by the "KBASE_ENDPOINT" environment
        variable, which must be set in order for the service to start.

        For user interfaces, unlike for services, we need the "origin" - that is the
        protocol and host.

        We make an explicit exception for the one environment, production, that breaks
        the rule that user interfaces operate on the same host as services.
        """
        endpoint_url = urlparse(self.kbase_endpoint)

        # We need to handle the ui endpoint for prod specially, as it operates
        # with the service host kbase.us and ui host narrative.kbase.us
        # The kbase-wide "KBASE_ENDPOINT" is for services, but from it we can
        # determine the ui endpoint.
        host = (
            "narrative.kbase.us"
            if endpoint_url.hostname == "kbase.us"
            else endpoint_url.netloc
        )
        return f"{endpoint_url.scheme}://{host}"


def get_service_description() -> ServiceDescription:
    file_path = os.path.join(
        ServiceConfig().runtime_config.service_directory, "SERVICE_DESCRIPTION.toml"
    )
    with open(file_path, "rb") as file:
        return ServiceDescription.model_validate(tomllib.load(file))


def get_git_info() -> GitInfo:
    path = os.path.join(
        ServiceConfig().runtime_config.service_directory, "build/git-info.json"
    )
    with open(path, "rb") as fin:
        return GitInfo.model_validate(json.load(fin))
