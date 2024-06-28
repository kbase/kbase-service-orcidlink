#
# Commonly used fields
#
from fastapi import Cookie, Path, Query
from pydantic import Field

from orcidlink.jsonrpc.errors import NotAuthorizedError, NotFoundError
from orcidlink.model import LinkingSessionComplete
from orcidlink.storage.storage_model import storage_model
from orcidlink.storage.storage_model_mongo import StorageModelMongo

SESSION_ID_FIELD = Field(
    description="The linking session id",
    # It is a uuid, whose string representation is 36 characters.
    min_length=36,
    max_length=36,
)
SESSION_ID_PATH_ELEMENT = Path(
    description="The linking session id",
    # It is a uuid, whose string representation is 36 characters.
    min_length=36,
    max_length=36,
)
RETURN_LINK_QUERY = Query(
    default=None,
    description="A url to redirect to after the entire linking is complete; "
    + "not to be confused with the ORCID OAuth flow's redirect_url",
)
SKIP_PROMPT_QUERY = Query(
    default=False, description="Whether to prompt for confirmation of linking"
)

UI_OPTIONS_QUERY = Query(default="", description="Opaque string of ui options")

KBASE_SESSION_COOKIE = Cookie(
    default=None,
    description="KBase auth token taken from a cookie named 'kbase_session'",
)

KBASE_SESSION_BACKUP_COOKIE = Cookie(
    default=None,
    description="KBase auth token taken from a cookie named 'kbase_session_backup. "
    + "Required in the KBase production environment since the prod ui and services "
    + "operate on different hosts; the primary cookie, kbase_session, is host-based "
    "so cannot be read by a prod service.",
)


async def get_linking_session_completed(
    model: StorageModelMongo, session_id: str, username: str
) -> LinkingSessionComplete:
    model = storage_model()

    session_record = await model.get_linking_session_completed(session_id)

    if session_record is None:
        raise NotFoundError("Linking session not found")

    if session_record.username != username:
        raise NotAuthorizedError("Username does not match linking session")

    return session_record
