# Deployment Quick Start

## Image

A production deployment image is tagged with the release semver 2.0 version. E.g.
`ghcr.io/kbase/kbase-service-orcidlink:v1.2.3`.

Evaluation of pull requests in CI or some other environment can be achieved with images
built from pull request activity, which have the form `ghcr.io/kbase/kbase-service-orcidlink-develop:pr-123`.

## Docker Command

All configuration is via environment variables. For Rancher, at least, there is no
need for a command, as the default entrypoint and command are adequate.

## Environment Variables

### Required

These environment variables do not have a default value so must be set before the
service is started. 


| Name           | Type | Default | Description | Example |
|----------------|------|---------|---|---|
| KBASE_ENDPOINT | str  |  n/a      |The base url for service calls in the current deployment environment. Note that it includes the "services" path and traditionall ends with a forward slash "/", although the service doesn't need it. | https://ci.kbase.us/services/ |
| MONGO_USERNAME | str | n/a | The username for the mongo database used by the orcidlink service | orcidlink_user |
| MONGO_PASSWORD | str | n/a | The password associated with the MONGO_USERNAME | secret_password |
| ORCID_API_BASE_URL | str | n/a | The base url to use for calls to the ORCID API | https://api.sandbox.orcid.org/v3.0 |
| ORCID_OAUTH_BASE_URL | str | n/a | The base url to use for calls to the ORCID OAuth API | https://sandbox.orcid.org/oauth |
| ORCID_SITE_BASE_URL | str | n/a | The base url to use for Links to the ORCID site | https://sandbox.orcid.org |
| ORCID_CLIENT_ID | str | n/a | The "client id" assigned by ORCID to  KBase for using with ORCID APIs | |
| ORCID_CLIENT_SECRET | str | n/a | The "client secret" assigned by ORCID to KBase for using with ORCID APIs | |

### Optional

All environment variables utilized are required. Several have defaults, however, which means that in practice the environment variables do not need to be provided. Still, it is best practice to provide values for all environment variables.

| Name           | Type | Default | Description | Example |
|----------------|------|---------|---|---|
| SERVICE_TIMEOUT | int | 600 | The duration, in *seconds*, after which a request to a network api is considered to have timed out. Such connections will be cancelled after the timeout and raise an error | |
| TOKEN_CACHE_LIFETIME | int | 600 | The duration, in *seconds*, for which KBase auth token state will be cached. Caching token state saves many calls to the auth service to validate a token. | |
| TOKEN_CACHE_MAX_ITEMS | int | 1000 | The maximum number of token state objects to retain in the cache; when the limit is reached, the least recently used items are removed to make space for new ones | | 
| MONGO_PORT | int | 27017 | The port for the mongo database server | 27017 |
| MONGO_DATABASE | str | orcidlink | The name of the mongo database associated with the orcidlink service | orcidlink |
| KBASE_SERVICE_AUTH | str | auth | The path to be joined to KBASE_ENVIRONMENT to form the url for the Auth Service | |
| KBASE_SERVICE_ORCID_LINK | str | orcidlink | The path to be joined to KBASE_ENVIRONMENT to form the url for the ORCID Link Service | |
| MANAGER_ROLE | str |ORCIDLINK_MANAGER | The "custom role" in KBase auth which gives a user the ability to use the management api and management interface | |
| LOG_LEVEL | str | INFO | The log level, in string form, to apply to all logging | DEBUG |


## Verifying deployment

In order to verify the version of a deployment, you may call the "info" method:

The following request:

```json
curl -X POST https://ci.kbase.us/services/orcidlink/api/v1 \
    -d '{
    "jsonrpc": "2.0",
    "id": "123",
    "method": "info"
}'
```

yields (extraneous information removed for brvty):

```json
{
    "result": {
        "service-description": {
            "name": "ORCIDLink",
            "version": "0.4.0",
        },
        "git-info": {
            "commit_hash": "5f3ba5ef40df1d6714550585984147e8d15a14a4",
            "author_name": "Erik Pearson",
            "author_date": 1697753050000,
            "committer_name": "GitHub",
            "committer_date": 1697753050000,
            "url": "https://github.com/kbase/kbase-service-orcidlink",
        }
    }
}
```