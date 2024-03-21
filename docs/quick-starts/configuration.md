# Configuration

All configuration for the orcidlink service is by environment variables and default values defined in `lib/config.py`.

That is, in contrast to some services, there is no "config template" that is built at server startup-time. Rather the server's start-up environment must have required enviromment variables defined. Optional enviroment variables have defaults defined in `lib/config.py`, which is also responsible for importing all environment variables into the runtime.

Configuration is made available throughout the service by way of `/lib/runtime.py`, which creates a config object and stores it in a module-level global variable. In order to solve the potential race condition, the `FastAPI` lifcycle mechanism is used to ensure that a service instance will import the configuration before any endpoints are handled.

## Service Endpoints

Only service endpoints actually utilized are encoded into the configuration. They are built during the config import process based on the ubiquitous `KBASE_ENDPOINT` environment variable and the "well known" service paths. Although service paths are meant to be configurable, in reality they have never changed once established.

So service endpoints are dynamnically built, but they can also be overridden by providing an explicity environment variable.

## The Environment Variables

There are quite a few environment variables. Some are standard and cover parameterization of common behavior like request timeout, kbase environment endpoint, and token caching.

Others are specific to this service, such as the linking session lifetime (ttl), orcid api credentials and urls, and mongo db credentials and configuration.

The [Deployment doc](../operation/deployment.md) has all the details.

## Development

During development, the required environment variables need to be mocked. The [development quick-start](./development.md) provides more details (but not a lot)

## Testing

The configuration must often be populated during testing. It is fairly easy to do so with Python's built-in unit test mocking.