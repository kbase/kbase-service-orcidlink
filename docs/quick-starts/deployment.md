# Deployment Quick Start

Topics covered:

- external dependencies: database, orcid
- image
- docker command
- environment variables
- custom auth role for managing
- verify a deployment

## External Dependencies

### Mongo Database

The service requires a mongo database. See below for configuration variables.
The database user assigned in the configuration should have the role `dbOwner`.

### ORCID

The service relies upon the availability of ORCID API, oAuth endpoints, and
general web site being available. ORCID maintains a sandbox environment, which
replicates almost all of their production environments, and is the appropriate
target when testing and evaluating the service and changes to it.

In order to use the API and OAuth, credentials are required. ORCID sandbox and
production have different endpoints, and require different credentials.

The credentials consist of the client id and secret. For the sandbox, an
individual developer may obtain credentials. The process, out of scope here,
starts with a form and thereafter is via email. The production credentials are
handled by our ORCID KBase Organization contact.

## Image

A production deployment image is tagged with the release semver 2.0 version. E.g.
`ghcr.io/kbase/kbase-service-orcidlink:v1.2.3`.

Evaluation of pull requests in CI or some other environment can be achieved with
images built from pull request activity, which have the form
`ghcr.io/kbase/kbase-service-orcidlink-develop:pr-123`.

## Docker Command

All configuration is via environment variables. For Rancher, at least, there is no
need for a command, as the default entrypoint and command are adequate.

## Environment Variables

### Required

These environment variables do not have a default value so must be set before the
service is started.

| Name                       | Type | Description                                                                            | Example                                      |
|----------------------------|------|----------------------------------------------------------------------------------------|----------------------------------------------|
| KBASE_ENDPOINT             | str  | The base url for service calls in the current deployment environment. [1](#footnote-1) | <https://ci.kbase.us/services/>              |
| MONGO_USERNAME             | str  | The username for the mongo database used by the orcidlink service                      | orcidlink_user                               |
| MONGO_PASSWORD             | str  | The password associated with the MONGO_USERNAME                                        | secret_password                              |
| ORCID_API_BASE_URL         | str  | The base url to use for calls to the ORCID API                                         | <https://api.sandbox.orcid.org/v3.0>         |
| ORCID_OAUTH_BASE_URL       | str  | The base url to use for calls to the ORCID OAuth API                                   | <https://sandbox.orcid.org/oauth>            |
| ORCID_SITE_BASE_URL        | str  | The base url to use for Links to the ORCID site                                        | <https://sandbox.orcid.org>                  |
| ORCID_CLIENT_ID            | str  | The "client id" assigned by ORCID to  KBase for using with ORCID APIs                  |                                              |
| ORCID_CLIENT_SECRET        | str  | The "client secret" assigned by ORCID to KBase for using with ORCID APIs               |                                              |
| LINKING_SESSION_RETURN_URL | str  | The full url to the url to return to after finishing [2](#footnote-2)                  | <https://ci.kbase.us/orcidlink/linkcontinue> |

<span id="footnote-1">[1]</span>  Note that it includes the "services" path and
traditionally ends with a forward slash "/", although the service doesn't need
it.

<span id="footnote-2">[1]</span>  This was added during co-development with
Europa, in order to facilitate easily switching back and forth between Europa
and kbase-ui. However, that is now moot, and it should be factored out. The line
where it is used in linking_sessions.py has the original implementation
commented out.

### Optional but recommended

These environment variables do have sensible defaults, but it is recommended
that they be utilized in the deployment settings so that they may be easily
overridden and understood at a glance.

| Name           | Type | Default   | Description                                                          | Example   |
|----------------|------|-----------|----------------------------------------------------------------------|-----------|
| MONGO_PORT     | int  | 27017     | The port for the mongo database server                               | 27017     |
| MONGO_DATABASE | str  | orcidlink | The name of the mongo database associated with the orcidlink service | orcidlink |
| LOG_LEVEL      | str  | INFO      | The log level, in string form, to apply to all logging               | DEBUG     |

### Optional

These environment variables all have sensible defaults and need not be specified
in the deployment.

| Name                     | Type | Default           | Description                                                                                                                                                                 | Example |
|--------------------------|------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| SERVICE_TIMEOUT          | int  | 600               | The duration, in *seconds*, after which a request to a network api is considered to have timed out. Such connections will be cancelled after the timeout and raise an error |         |
| TOKEN_CACHE_LIFETIME     | int  | 600               | The duration, in *seconds*, for which KBase auth token state will be cached. Caching token state saves many calls to the auth service to validate a token.                  |         |
| TOKEN_CACHE_MAX_ITEMS    | int  | 1000              | The maximum number of token state objects to retain in the cache; when the limit is reached, the least recently used items are removed to make space for new ones           |         |
| KBASE_SERVICE_AUTH       | str  | auth              | The path to be joined to KBASE_ENDPOINT to form the url for the Auth Service                                                                                                |         |
| KBASE_SERVICE_ORCID_LINK | str  | orcidlink         | The path to be joined to KBASE_ENDPOINT to form the url for the ORCID Link Service                                                                                          |         |
| MANAGER_ROLE             | str  | ORCIDLINK_MANAGER | The "custom role" in KBase auth which gives a user the ability to use the management api and management interface                                                           |         |

## Custom Role for Management

The ORCID Link service and front-end support a basic level of management. This
capability is unlocked for a user via the "ORCIDLINK_MANAGER" custom auth role.

Thus, for a fresh deployment, this role needs to be created, and then assigned
to whoever needs it.

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

yields:

```json
{
    "jsonrpc": "2.0",
    "result": {
        "service-description": {
            "name": "ORCIDLink",
            "title": "ORCID Link",
            "version": "0.4.0",
            "language": "Python",
            "description": "A service for creating linkage between a KBase account and an ORCID account.\n\nIf a linkage, known herein as an \"ORCID Link\", exists for a user, the following features are available:\n    - read the associated ORCID profile, including just public and trusted partner keys\n    - read, create, update, and delete work activity (publications)\n    - remove ORCID Link\n",
            "repoURL": "https://github.com/kbase/kbase-service-orcidlink"
        },
        "git-info": {
            "commit_hash": "5257ce20c469e75199ebeff56419ad6ed22596ae",
            "commit_hash_abbreviated": "5257ce2",
            "author_name": "Erik Pearson",
            "author_date": 1710979626000,
            "committer_name": "GitHub",
            "committer_date": 1710979626000,
            "url": "https://github.com/kbase/kbase-service-orcidlink",
            "branch": "HEAD",
            "tag": null
        },
        "runtime_info": {
            "current_time": 1713207945769,
            "orcid_api_url": "https://api.orcid.org/v3.0",
            "orcid_oauth_url": "https://orcid.org/oauth",
            "orcid_site_url": "https://orcid.org"
        }
    },
    "id": "123"
}
```
