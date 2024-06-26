# ORCID Link  _(kbase-service-orcidlink)_

*ORCID Link* is a KBase core REST service whose primary purpose is to link KBase accounts to ORCID accounts.

ORCID Link also provides additional functionality such as fetching the profile for a linked account, and managing the "works" for a linked account

The service is implemented in Python, using the FastAPI library.

Please see the [design doc](docs/design/design.md) for further information.

## Security

This service will only start with a specific set of [environment variables](docs/operation/deployment.md#environment-variables), some of which contain private keys essential for communication with ORCID Services. See [the deploymet doc](docs/operation/deployment.md) for details.

## Background

Many users of KBase also [ORCID (Open Researcher and Contributor ID)](https://orcid.org) users as well. There are many opportunities for synergy between KBase and ORCID with respect to their users. Examples include:

- **profile synchronization**: An ORCID account is designed to serve as a canonical profile; as such, a KBase profile is not only redundant, but may be in conflict; KBase can use a user's associated ORCID profile to synchronize with or replace the KBase profile.
- **automated publication**: KBase is a platform supporting publication of analysis documents termed "Narratives", as well as the publication of openly accessible data. A KBase user who publishes Narratives and data and obtains a [DOI](https://doi.org), may use KBase tools to automatically populate and manage the "works" section of their profile.

By linking a KBase account to an ORCID account, tools described above can be implemented, to the benefit of KBase users.

## Installation

This service is not directly installable as such. It is a REST-based web service and must be built and run within a compatible deployment environment.

One could say that "installation" consists of building a Docker image and hosting it somewhere. In practice, this is conducted at GitHub, with a build conducted by [GitHub Actions](docs/operation/deployment.md#github-actions) and hosted at the [GitHub Container Repository (GHCR)](https://ghcr.io), also known as [GitHub Packages](https://github.com/features/packages).

## Usage

There are different scenarios under which _ORCID Link_ may be run and utilized. Each is described in separate sections:

- [development](docs/development/development.md)
- [deployment](docs/operation/deployment.md)

Deployment support is generally described, but deployment practices and mechanics are out of scope of this document and service.

Running as a local service is not only feasible but the normal model for development.

## API

The [API docs](docs/api/index.md) are generated automatically, and are [available in the codebase](docs/api/index.md) as well as from a live instance of the service at the `/docs` endpoint.

## Contributing

For supported and recommended development practices see [development](docs/development/development.md).

## License

See license in [LICENSE.md](LICENSE.md)
