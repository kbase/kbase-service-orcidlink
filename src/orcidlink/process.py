from typing import Optional

from orcidlink.jsonrpc.errors import NotAuthorizedError, NotFoundError
from orcidlink.lib.service_clients.orcid_oauth_api import orcid_oauth_api
from orcidlink.lib.utils import posix_time_millis
from orcidlink.model import LinkingSessionInitial, LinkingSessionStarted, LinkRecord
from orcidlink.runtime import config
from orcidlink.storage.storage_model import storage_model


async def delete_link(username: str) -> None:
    """
    Deletes the a linking record for a given user.
    """
    storage = storage_model()
    link_record = await storage.get_link_record(username)

    if link_record is None:
        raise NotFoundError("User does not have an ORCID Link")

    # TODO: handle error? or propagate? or in a transaction?
    await orcid_oauth_api().revoke_access_token(link_record.orcid_auth.access_token)

    # TODO: handle error? or propagate?
    await storage.delete_link_record(username)


async def link_record_for_user(username: str) -> Optional[LinkRecord]:
    #
    # Fetch the user's ORCID Link record from KBase.
    #
    user_link_record = await storage_model().get_link_record(username)
    if user_link_record is None:
        return None

    # Make sure the orcid auth is not retired.
    now = posix_time_millis()
    if user_link_record.retires_at < now:
        user_link_record = await refresh_token_for_link(user_link_record)

    return user_link_record


async def link_record_for_orcid_id(orcid_id: str) -> Optional[LinkRecord]:
    #
    # Fetch the user's ORCID Link record from KBase.
    #
    user_link_record = await storage_model().get_link_record_for_orcid_id(orcid_id)
    if user_link_record is None:
        return None
        # raise exceptions.ServiceErrorY(
        #     error=errors.ERRORS.not_found, message="ORCID Profile Not Found"
        # )

    # Make sure the orcid auth is not retired.
    now = posix_time_millis()
    if user_link_record.retires_at < now:
        user_link_record = await refresh_token_for_link(user_link_record)

    return user_link_record


async def refresh_token_for_link(link_record: LinkRecord) -> LinkRecord:
    now = posix_time_millis()

    # refresh the tokens
    orcid_auth = await orcid_oauth_api().refresh_token(
        link_record.orcid_auth.refresh_token
    )

    link_record.orcid_auth = orcid_auth
    link_record.created_at = posix_time_millis()
    link_record.expires_at = (
        link_record.created_at + config().linking_session_lifetime * 1000
    )
    link_record.retires_at = now + config().orcid_authorization_retirement_age * 1000

    # update the link with the new orcid_auth
    await storage_model().save_link_record(link_record)

    return link_record


async def get_linking_session_initial(
    session_id: str, username: str
) -> LinkingSessionInitial:
    model = storage_model()

    session_record = await model.get_linking_session_initial(session_id)

    if session_record is None:
        raise NotFoundError("Linking session not found")

    if not session_record.username == username:
        raise NotAuthorizedError("Username does not match linking session")

    return session_record


async def get_linking_session_started(
    session_id: str, username: str
) -> LinkingSessionStarted:
    model = storage_model()

    session_record = await model.get_linking_session_started(session_id)

    if session_record is None:
        raise NotFoundError("Linking session not found")

    if not session_record.username == username:
        raise NotAuthorizedError("Username does not match linking session")

    return session_record
