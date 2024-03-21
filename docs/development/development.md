# Development

## Getting Started

1.  install git hooks

Git hooks are a convenience, but not a requirement. Currently, there is a pre-commit and pre-push hook. The pre-commit runs the same code checks as the GHA workflows do, and the pre-push runs the tests.

```shell
git config --local core.hooksPath .githooks/
```

2. A convenience...

As all development tasks are automated with `Taskfile`. Rather than invoke it with `./Taskfile task`, you can create an alias and invoke it as `run task`:

```shell
alias run="${PWD}/Taskfile"
```

3. run code checks and tests

It is a good idea to start any development session by running the code checks and tests. This ensures you are starting in a clean, well-functioning state.

```shell
run mypy
run black
run test
```

## Running server locally 

build image

```shell
./Taskfile build-image
```

run image

> doesn't work as is -- needs mongo!

```shell
ORCID_CLIENT_ID='AAA' ORCID_CLIENT_SECRET='BBB' ./Taskfile run-image
```

## Running server locally with kbase-ui

> TODO 

## Contributing

All development is orchestrated through the GitHub repo roughly following the *gitflow* git workflow.

Contributions should be made via a branch off of the develop branch. Such branches should normally be created in response to a KBase JIRA ticket, but can also be related to a GitHub issue. The contribution branch should be pushed directly to the kbase repo, certainly for staff; outside contributions will need to be from forks.

When the branch is ready for review, a PR is made from the contribution branch to the develop branch. The PR description template lists all of the requirements. When those requirements are met, and tests pass, a review should be requested.

Upon approval, the PR will be merged into the develop branch.

Periodically, or as needed, the state of the develop branch will be deployed to the CI environment, https://ci.kbase.us.

At some point in the future, when a release is called for, the develop branch will be merged into the master branch, a release created, and the resulting image deployed to the next environment, appdev, and ultimately production.

## GitHub Action Workflows

When changes are made to the repo at GitHub, GitHub Actions (GHA) may be invoked to perform tests, an image build, and a push of the resulting image to GitHub Container Registry (GHCR).

It is useful to understand exactly when the GHA workflows are triggered and what they do, because you should monitor the results to ensure that everything that should have happened, has indeed occurred.

### Top level workflows

| # | KBase? | Name                            | Filename                  | 
|---|--------|---------------------------------|---------------------------|
| 1 | ✓      | Pull Request Build, Tag, & Push | pr_build.yml              | 
| 2 | ✓      | Release - Build & Push Image    | release-main.yml          |
| 3 | ✓      | Manual Build & Push             | manual-build.yml          |
| 4 |        | Code Checks & Tests             | code-checks-and-tests.yml |

#### Kbase workflows

KBase workflows are provided through the kbase GitHub organization. They should be copied verbatim into the .github/workflows directory and used as-is. They utilize reusable workflows that are stored in the kbase organization. (That is, you won't see them in your repo.) The kbase reusable workflows may change over time.

##### Pull Request Build, Tag, & Push

Handles pull request activity on main, master, and develop branches. The activities include opened, reopened, synchronize, and closed. Conditional workflow jobs handle more fine-grained triggering. 

For example, the `build-develop-open` job only applies to the develop branch and for a PR action which does not involve a merge, and only performs a build, not a push.

See the workflow file for all triggers and consequences (summarized in the table below).

##### Release - Build & Push Image

This workflow file handles a release on the main or master branch, and results in a build and push.

##### Manual Build & Push

This workflow may be triggered manually on any branch. It results in a build and push.

#### Workflows in this service only

##### Code Checks & Tests

The KBase workflows do not contain any requirements for testing, so each service must supply a workflow which performs code checks and tests.

This workflow is triggered by the same conditions as the KBase workflows.

The detachment of test from build has consequences for the "workflow" with GitHub. 

- two workflows are run for each trigger - the KBase build & push and the orcidlink code checks & tests
- the build & push workflow will proceed even if tests fail
- a manual workflow run for orcidlink's "Code Checks & Tests" needs to be run separately from the KBase "Manual Build & Push". (This is the way manual workflows work -- a manual trigger does not trigger all manual workflows!)

### Triggering conditions and consequences

| # | branch  | triggering condition     | test | build | push | image name                      | image tag                      |
|---|---------|--------------------------|------|-------|------|---------------------------------|--------------------------------|
| 1 | develop | pr activity <sup>1</sup> | ✓    | ✓     |      |                                 |                                |
| 2 | develop | pr merged                | ✓    | ✓     | ✓    | kbase-service-orcidlink-develop | latest, pr-_#_ <sup>2</sup>    |
| 3 | main    | pr activity              | ✓    | ✓     | ✓    | kbase-service-orcidlink         | pr-_#_ <sup>2</sup>            |
| 4 | main    | pr merged                | ✓    | ✓     | ✓    | kbase-service-orcidlink         | latest-rc, pr-_#_ <sup>2</sup> |
| 5 | main    | release                  | ✓    | ✓     | ✓    | kbase-service-orcidlink         | latest, _#.#.#_ <sup>3</sup>   |
| 6 | any     | manual <sup>5</sup>      | ✓    | ✓     | ✓    | kbase-service-orcidlink-develop | br-_branch_ <sup>4</sup>       |
| 7 | any     | manual <sup>6</sup>      | ✓    |       |      |                                 | br-_branch_ <sup>4</sup>       |

<sup>1</sup> activity defined as "opened", "reopened", "synchronize"   
<sup>2</sup> where _#_ is the pull request number  
<sup>3</sup> where _#.#.#_ is the semver 2 formatted version  
<sup>4</sup> where _branch_ is the branch name upon which the manual workflow was run  
<sup>5</sup> when running "Manual Build & Push" workflow  
<sup>6</sup> when running "Code Checks and Tests" workflow

For those new to the way KBase core service workflows run, let us explain idiosyncracies.

### Two image names

There are **two image names** used. The canonical one, `kbase-service-orcidlink`, results from activity against the `main` branch. The second one is `kbase-service-orcidlink-develop`, which results from activity against the `develop` branch, as well as manual triggering of the "Manual Build & Push" workflow.

### Images from Pull Requests

As can be seen in the table above, several workflow conditions tag images with the pull request number.

### Separate test workflow

Since we have the condition that the Kbase 


 

## A workflow

### Use & Develop

- deploy this service locally, backed by MongoDB
- run kbase-ui locally, configured to use this service locally
- deployed with reload-on-change 
- develop demo calls via RESTer in Firefox
- need some secrets to run against ORCID Sandbox.

