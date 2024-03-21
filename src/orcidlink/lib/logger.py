import json
import logging
import uuid
from typing import Any

from orcidlink.lib.utils import posix_time_millis


class JSONLogger:
    directory: str
    name: str

    def __init__(self, directory: str, name: str):
        self.directory = directory
        self.name = name

    def get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        if len(logger.handlers) == 0:
            # Here we may change the logging handler to something like HTTP, syslog, io stream,
            # see https://docs.python.org/3/library/logging.handlers.html
            handler = logging.FileHandler(f"{self.directory}/{self.name}.log")
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_level(self, level: int) -> None:
        self.get_logger().setLevel(level)

    def log_event(self, event: str, data: Any, level: int = logging.INFO) -> str:
        # We use a separate logger, configured to save the
        # entire message as a simple string ... and that string
        # is a JSON-encoded message object.
        # The resulting log file, then, is y it is a JSON stream format, since it
        # contains multiple objects in sequence.
        log_id = str(uuid.uuid4())
        message = json.dumps(
            {
                # If logs are combined, we need to tie log entries to
                # a specific version of a service in a specific environment.
                "service": "orcidlink",
                "version": "n/a",
                "environment": "n/a",
                # General log entry; information that any log entry
                # will need.
                # id helps create a unique reference to a log entry; perhaps
                # should be uuid, service + uuid, or omitted and only created
                # by a logging repository service.
                "id": log_id,
                "timestamp": posix_time_millis(),
                # The actual, specific event. The event name is a simple
                # string, the data is a dict or serializable class whose
                # definition is implied by the event name.
                "event": {
                    "name": event,
                    # the event context captures information common to instances
                    # of this kind of event. As a narrative ui event, part of the context
                    # is the narrative object, the current user, and the current user's
                    # browser. Clearly more could be captured here, e.g. the browser model,
                    # narrative session id, etc.
                    "context": {
                        # I tried to update kbase_env to reflect the current narrative ref,
                        # but to no avail so far. The kbase_env here is not the same as the
                        # one used when saving a narrative and getting the new version, so it does
                        # not reflect an updated narrative object version.
                        # If that isn't possible, we can store the ws and object id instead.
                        # "narrative_ref": kbase_env.narrative_ref,
                        # Log entries for authenticated contexts should identify the user
                        "username": "n/a",
                        # Log entries resulting from a network call can/should identify
                        # the ip address of the caller
                        "client_ip": "n/a",
                        # could be more context, like the jupyter / ipython / etc. versions
                    },
                    # This is the specific data sent in this logging event
                    "data": data,
                },
            }
        )

        self.get_logger().log(level, message)

        return log_id


ORCID_LOGGER = JSONLogger("/tmp", "orcidlink")


def log_level(level: int) -> None:
    ORCID_LOGGER.log_level(level)


def log_event(event: str, data: Any, level: int = logging.INFO) -> str:
    return ORCID_LOGGER.log_event(event, data, level)
