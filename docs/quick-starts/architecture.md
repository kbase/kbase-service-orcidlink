# Architecture

The `orcidlink` service operates as an async Python web service. It accesses data in a `mongodb` database. 

Configuration is by way of environment variables.

## Service Runtime

The service is implemented with the `FastAPI` web framework. This is an asynchronous server utilizing Pydantic for strict typing and automatic creation of openapi specs, jsonschema, and documentation. The server is managed by `uvicorn`, an "ASGI" web server, specialized in manager aysnc web frameworks like FastAPI.

The implementation code leverages asynchronous operations for all i/o. This is important as otherwise non-threaded async servers can lock up with long-running blocking i/o operations (or time-consuming CPU operations). Therefore, all code which deals with the file system and especially external network api calls, is asynchronous.

## Configuration

All configuration is by way of environment variables, with a smattering of heuristics. There is no "config template" file, rather the service reads environment variables at start-up time and populates a global runtime configuration object.

All configurable properties may be provided explicitly as environment variables, although many of them have defaults or are heuristically determined. These measures alleviate the need to explicitly configure everything.

Service urls (e.g. auth, workspace) are configured from the KBase environment's endpoint (`KBASE_ENDPOINT`) and their well-known paths, but they may also be overridden with an environment variable.

Similarly, the `UI_ORIGIN` - the base url for all user interface urls in the KBase environment - is built from the service endpoint with an exception for production, yet may also be overridden with the environment variable.

## Errors

All errors returned are defined in a single location, the `errors.py` module. Due to the nature of a web app, and FastAPI in particular, some errors are raised as exceptions within implementation code (e.g. auth failure), some raised as exceptions by FastAPI (e.g. 404), and some are simply returned by the endpoint handlers. 

Errors have at a minimum an integer `code`, and a string `message`. Some errors may have associated data, but I've tried to minimize this.

## Service Initialization and Database Migration

When first started, the service will attempt to connect to the database and load the service description document. If there is a version difference between this document and the service description stamped into the codebase (`SERVICE_DESCRIPTION.toml`), a database migration may be performed. Database migrations are defined only between two adjacent versions. 

Essentially, upon started the database is either initialized from scratch or migrated.

At present there is now downgrade migration.

## Database Maintenance

During the ORCID Link user process, a document is created to represent the linking session. If a linking session is interrupted (e.g. the user decides to just close their browser), these linking session documents will remain in the database.

Although there is no harm from these "danging documents", it is good practice to remove them. A linking session has a 10-minute time limit. A background process kicks off every minute or to inspect the database and will remove any linking session documents which are more than 10 minutes old.