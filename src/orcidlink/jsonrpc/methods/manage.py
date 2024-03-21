from typing import Any, Dict, List, Optional, Union

import pymongo
from pydantic import Field

from orcidlink.jsonrpc.errors import NotAuthorizedError, NotFoundError
from orcidlink.lib.service_clients.kbase_auth import AccountInfo
from orcidlink.lib.service_clients.orcid_oauth_api import orcid_oauth_api
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.lib.utils import posix_time_millis
from orcidlink.model import (
    LinkingSessionCompletePublic,
    LinkingSessionInitial,
    LinkingSessionStarted,
    LinkRecordPublic,
)
from orcidlink.runtime import config
from orcidlink.storage.storage_model import storage_model
from orcidlink.storage.storage_model_mongo import StatsRecord


class IsManagerResult(ServiceBaseModel):
    is_manager: bool = Field(...)


async def is_manager(username: str, account_info: AccountInfo) -> IsManagerResult:
    if username != account_info.user:
        raise NotAuthorizedError()

    if config().manager_role not in account_info.customroles:
        return IsManagerResult(is_manager=False)
        # raise exceptions.UnauthorizedError("Not authorized for management operations")

    return IsManagerResult(is_manager=True)


# Search for Links


class FindLinksResult(ServiceBaseModel):
    links: List[LinkRecordPublic]


class FilterByUsername(ServiceBaseModel):
    eq: Optional[str] = Field(default=None)
    contains: Optional[str] = Field(default=None)


class FilterByORCIDId(ServiceBaseModel):
    eq: str = Field(...)


class FilterByEpochTime(ServiceBaseModel):
    eq: Optional[int] = Field(default=None)
    gte: Optional[int] = Field(default=None)
    gt: Optional[int] = Field(default=None)
    lte: Optional[int] = Field(default=None)
    lt: Optional[int] = Field(default=None)


class FilterByCreationTime(FilterByEpochTime):
    pass


class FilterByExpirationTime(FilterByEpochTime):
    pass


class QueryFind(ServiceBaseModel):
    username: Optional[FilterByUsername] = Field(default=None)
    orcid: Optional[FilterByORCIDId] = Field(default=None)
    created: Optional[FilterByCreationTime] = Field(default=None)
    expires: Optional[FilterByExpirationTime] = Field(default=None)

    class Config:  # type: ignore
        extra = "forbid"


class QuerySortSpec(ServiceBaseModel):
    field_name: str = Field(...)
    descending: Optional[bool] = Field(default=None)


class QuerySort(ServiceBaseModel):
    specs: List[QuerySortSpec] = Field(...)


class SearchQuery(ServiceBaseModel):
    find: Optional[QueryFind] = Field(default=None)
    sort: Optional[QuerySort] = Field(default=None)
    offset: Optional[int] = Field(default=None)
    limit: Optional[int] = Field(default=None)

    class Config:  # type: ignore
        extra = "forbid"


def augment_with_time_filter(
    filter: Dict[str, Dict[str, Union[str, int]]],
    field_name: str,
    possible_filter: Optional[FilterByEpochTime],
) -> Any:
    """
    Given a
    """
    if possible_filter is None:
        return filter

    if possible_filter.eq is not None:
        filter[field_name] = {"$eq": possible_filter.eq}
    if possible_filter.gt is not None:
        filter[field_name] = {"$gt": possible_filter.gt}
    if possible_filter.gte is not None:
        filter[field_name] = {"$gte": possible_filter.gte}
    if possible_filter.lt is not None:
        filter[field_name] = {"$lt": possible_filter.lt}
    if possible_filter.lte is not None:
        filter[field_name] = {"$lte": possible_filter.lte}

    return filter


async def find_links(query: Optional[SearchQuery] = None) -> FindLinksResult:
    filter: dict[str, dict[str, str | int]] = {}
    sort: list[tuple[str, int]] = []
    offset = 0
    limit = None

    if query:
        if query.find is not None:
            if query.find.username is not None:
                if query.find.username.eq is not None:
                    filter["username"] = {"$eq": query.find.username.eq}

            if query.find.orcid is not None:
                filter["orcid_auth.orcid"] = {"$eq": query.find.orcid.eq}

            augment_with_time_filter(filter, "created_at", query.find.created)
            augment_with_time_filter(filter, "expires_at", query.find.expires)

        if query.sort is not None:
            for sort_spec in query.sort.specs:
                sort.append(  # type: ignore
                    (
                        sort_spec.field_name,
                        (
                            pymongo.DESCENDING
                            if sort_spec.descending is True
                            else pymongo.ASCENDING
                        ),
                    )
                )

        if query.offset is not None:
            offset = query.offset

        if query.limit is not None:
            # TODO: place reasonable limits on this
            limit = query.limit

    model = storage_model()
    links = await model.get_link_records(
        filter=filter, sort=sort, offset=offset, limit=limit
    )

    public_links = [
        LinkRecordPublic.model_validate(link.model_dump()) for link in links
    ]

    return FindLinksResult(links=public_links)


class GetLinkResult(ServiceBaseModel):
    link: LinkRecordPublic


async def get_link(username: str) -> GetLinkResult:
    model = storage_model()
    link_record = await model.get_link_record(username)

    if link_record is None:
        raise NotFoundError("No link record was found for this user")

    return GetLinkResult(link=LinkRecordPublic.model_validate(link_record.model_dump()))


class GetLinkingSessionsResult(ServiceBaseModel):
    initial_linking_sessions: List[LinkingSessionInitial]
    started_linking_sessions: List[LinkingSessionStarted]
    completed_linking_sessions: List[LinkingSessionCompletePublic]


async def get_linking_sessions() -> GetLinkingSessionsResult:
    model = storage_model()
    initial_linking_sessions = await model.get_linking_sessions_initial()
    started_linking_sessions = await model.get_linking_sessions_started()
    completed_linking_sessions = await model.get_linking_sessions_completed()

    completed_linking_sessions_public = [
        LinkingSessionCompletePublic.model_validate(linking_session.model_dump())
        for linking_session in completed_linking_sessions
    ]

    return GetLinkingSessionsResult(
        initial_linking_sessions=initial_linking_sessions,
        started_linking_sessions=started_linking_sessions,
        completed_linking_sessions=completed_linking_sessions_public,
    )


async def delete_expired_linking_sessions() -> None:
    model = storage_model()

    now = posix_time_millis()

    expired_sessions = await model.get_expired_sessions(now)

    for expired_completed_session in expired_sessions.completed_sessions:
        await orcid_oauth_api().revoke_access_token(
            expired_completed_session.orcid_auth.access_token
        )

    # TODO: rectify with the above.
    await model.delete_expired_sessions()


async def delete_linking_session_initial(session_id: str) -> None:
    model = storage_model()
    await model.delete_linking_session_initial(session_id)


async def delete_linking_session_started(session_id: str) -> None:
    model = storage_model()
    await model.delete_linking_session_started(session_id)


async def delete_linking_session_completed(session_id: str) -> None:
    model = storage_model()
    await model.delete_linking_session_completed(session_id)


class GetStatsResult(ServiceBaseModel):
    stats: StatsRecord


async def get_stats() -> GetStatsResult:
    model = storage_model()
    stats = await model.get_stats()

    return GetStatsResult(stats=stats)


class RefreshTokensResult(ServiceBaseModel):
    link: LinkRecordPublic


async def refresh_tokens(username: str) -> RefreshTokensResult:
    storage = storage_model()
    link_record = await storage.get_link_record(username=username)

    if link_record is None:
        raise NotFoundError("Link record not found for this user")

    # refresh the tokens
    orcid_auth = await orcid_oauth_api().refresh_token(
        link_record.orcid_auth.refresh_token
    )

    link_record.orcid_auth = orcid_auth
    link_record.created_at = posix_time_millis()
    link_record.expires_at = (
        link_record.created_at + config().linking_session_lifetime * 1000
    )

    # update the link with the new orcid_auth
    await storage.save_link_record(link_record)

    return RefreshTokensResult(
        link=LinkRecordPublic.model_validate(link_record.model_dump())
    )
