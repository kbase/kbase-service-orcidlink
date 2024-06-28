FROM python:3.12.4-slim-bookworm
# Note that the python version needs to match that used to create
# poetry.lock.

MAINTAINER KBase Developer
LABEL org.opencontainers.image.source = "https://github.com/kbase/kbase-service-orcidlink"
LABEL org.opencontainers.image.description="A KBase core service to provide for linking a KBase account to an ORCID account, and associated services"
LABEL org.opencontainers.image.licenses=MIT

# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.
# -----------------------------------------

# We need curl to install poetry; git for the git-info tool.
RUN apt-get update && apt-get install -y curl git

SHELL ["/bin/bash", "-c"]

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.2

# Temporary fix for broken Python venv.
# setuptools is not used by poetry (see the install command below), but it is present
# anyway in poetry's venv (which is separate from that for the service). However, a bug
# in Python 3.11.1 (and perhaps others, I just confirmed with this version) installs the
# wrong version of setup tools -- it installs 65.5.0 from 3.11, which has a CVE issued
# against it. Just upgrading to the latest version, to avoid having to fix this when poetry's
# venv has a more recent version than 65.5.1 (which fixes the CVE). When the upstream issue is fixed,
# this line can be removed.
# TODO: can it be removed now?
RUN cd /root/.local/share/pypoetry && source venv/bin/activate && pip install --upgrade setuptools

# Annoyingly it puts it here.
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/kb/module/src"

RUN mkdir -p /kb/module/work && mkdir /kb/module/deploy && mkdir -p /kb/module/build  && chmod -R a+rw /kb/module

# Copying only files needed for service runtime.
# Other usages of this image, e.g. testing, mount the project root at /kb/module
# and have access to everything.
COPY ./scripts /kb/module/scripts
COPY ./src/orcidlink /kb/module/src/orcidlink
COPY ./src/boot /kb/module/src/boot
COPY ./src/misc /kb/module/src/misc
COPY ./schema /kb/module/schema
COPY ./poetry.lock /kb/module
COPY ./pyproject.toml /kb/module
COPY ./SERVICE_DESCRIPTION.toml /kb/module
COPY .git /kb/module
COPY ./log_config.yaml /kb/module

WORKDIR /kb/module

RUN poetry config virtualenvs.create false && poetry config virtualenvs.options.no-setuptools true && poetry install --no-dev

RUN poetry run python src/misc/git-info.py

# Don't need curl or git any more.
RUN apt-get purge -y curl git && apt-get autoremove -y

RUN rm -rf /kb/module/.git && rm -rf /kb/module/src/misc

RUN apt-get remove -y git

ENTRYPOINT [ "scripts/entrypoint.sh" ]

CMD [ "scripts/start-server.sh" ]