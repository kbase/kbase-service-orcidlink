from typing import Any, List, Optional

import motor.motor_asyncio

from orcidlink.jsonrpc.errors import NotFoundError

# from orcidlink.lib import errors, exceptions
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.lib.utils import posix_time_millis
from orcidlink.model import (
    LinkingSessionComplete,
    LinkingSessionInitial,
    LinkingSessionStarted,
    LinkRecord,
    ORCIDAuth,
)


class LinkStats(ServiceBaseModel):
    last_24_hours: int
    last_7_days: int
    last_30_days: int
    all_time: int


class LinkSessionStats(ServiceBaseModel):
    active: int
    expired: int


class StatsRecord(ServiceBaseModel):
    links: LinkStats
    linking_sessions_initial: LinkSessionStats
    linking_sessions_started: LinkSessionStats
    linking_sessions_completed: LinkSessionStats


class ExpiredSessions(ServiceBaseModel):
    initial_sessions: List[LinkingSessionInitial]
    started_sessions: List[LinkingSessionStarted]
    completed_sessions: List[LinkingSessionComplete]


class StorageModelMongo:
    def __init__(
        self, host: str, port: int, database: str, username: str, password: str
    ):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            host=host,
            port=port,
            username=username,
            password=password,
            authSource=database,
            retrywrites=False,
        )
        self.db = self.client[database]

    ##
    # Operations on the user record.
    # The user record is the primary linking document, providing a linkage between
    # a username and an ORCID Id.
    #
    async def get_link_record(self, username: str) -> Optional[LinkRecord]:
        record = await self.db.links.find_one({"username": username})

        if record is None:
            return None

        return LinkRecord.model_validate(record)

    async def get_link_records(
        self,
        filter: Optional[Any] = None,
        sort: Optional[Any] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[LinkRecord]:
        """
        Gets link records, optionally filtered by a search condition, sorted, and
        with a given range by offset and limit.

        Currently none of the options are implemented, and it returns all link records.

        This feature is designed for usage by management tools.
        """
        cursor = self.db.links.find(
            filter=filter if filter is not None else {},
            sort=sort if sort is not None else [],
            skip=offset or 0,
            limit=limit or 0,
        )

        links: List[LinkRecord] = []

        for doc in await cursor.to_list(length=100):
            link = LinkRecord.model_validate(doc)
            links.append(link)

        return links

    async def get_link_record_for_orcid_id(self, orcid_id: str) -> Optional[LinkRecord]:
        record = await self.db.links.find_one({"orcid_auth.orcid": orcid_id})

        if record is None:
            return None

        return LinkRecord.model_validate(record)

    async def save_link_record(self, record: LinkRecord) -> None:
        await self.db.links.update_one(
            {"username": record.username}, {"$set": record.model_dump()}
        )

    async def create_link_record(self, record: LinkRecord) -> None:
        await self.db.links.insert_one(record.model_dump())

    async def delete_link_record(self, username: str) -> None:
        await self.db.links.delete_one({"username": username})

    ################################
    # OAuth state persistence
    ################################

    # Linking session
    # TODO: operate with the linking session record model, not raw dict.

    async def create_linking_session(
        self, linking_record: LinkingSessionInitial
    ) -> None:
        await self.db.linking_sessions_initial.insert_one(linking_record.model_dump())

    async def delete_linking_session_initial(self, session_id: str) -> None:
        # The UI api only supports deleting completed sessions.
        # We'll need an admin API to delete danging initial and started linking
        # sessions.
        await self.db.linking_sessions_initial.delete_one({"session_id": session_id})

    async def delete_linking_session_started(self, session_id: str) -> None:
        # The UI api only supports deleting completed sessions.
        # We'll need an admin API to delete danging initial and started linking
        # sessions.
        await self.db.linking_sessions_started.delete_one({"session_id": session_id})

    async def delete_linking_session_completed(self, session_id: str) -> None:
        # The UI api only supports deleting completed sessions.
        # We'll need an admin API to delete danging initial and started linking
        # sessions.
        await self.db.linking_sessions_completed.delete_one({"session_id": session_id})

    # async def delete_expired_sessionsx(self) -> None:
    #     now = posix_time_millis()

    #     # For now, we fetch the docs, then delete them.
    #     # This will allow us to provide an audit trail.
    #     # If we don't implement an audit trail, we can just delete with the
    #     # find expression.
    #     initialized = self.db.linking_sessions_initial.find(
    #         {"expires_at": {"$lte": now}}
    #     )
    #     started = self.db.linking_sessions_started.find({"expires_at": {"$lte": now}})
    #     completed = self.db.linking_sessions_completed.find(
    #         {"expires_at": {"$lte": now}}
    #     )

    #     for session in await initialized.to_list(length=100):
    #         await self.db.linking_sessions_initial.delete_one(
    #             {"session_id": {"$eq": session.get("session_id")}}
    #         )

    #     for session in await started.to_list(length=100):
    #         await self.db.linking_sessions_started.delete_one(
    #             {"session_id": {"$eq": session.get("session_id")}}
    #         )

    #     for session in await completed.to_list(length=100):
    #         await self.db.linking_sessions_completed.delete_one(
    #             {"session_id": {"$eq": session.get("session_id")}}
    #         )

    async def delete_expired_sessions(self) -> None:
        now = posix_time_millis()

        await self.db.linking_sessions_initial.delete_many(
            {"expires_at": {"$lte": now}}
        )

        await self.db.linking_sessions_started.delete_many(
            {"expires_at": {"$lte": now}}
        )

        await self.db.linking_sessions_completed.delete_many(
            {"expires_at": {"$lte": now}}
        )

    async def get_expired_initial_sessions(
        self, now: int
    ) -> List[LinkingSessionInitial]:
        initial_sessions_cursor = self.db.linking_sessions_initial.find(
            {"expires_at": {"$lte": now}}
        )
        linking_sessions_initial: List[LinkingSessionInitial] = []
        for doc in await initial_sessions_cursor.to_list(length=100):
            link = LinkingSessionInitial.model_validate(doc)
            linking_sessions_initial.append(link)

        return linking_sessions_initial

    async def get_expired_started_sessions(
        self, now: int
    ) -> List[LinkingSessionStarted]:
        started_sessions_cursor = self.db.linking_sessions_started.find(
            {"expires_at": {"$lte": now}}
        )
        linking_sessions_started: List[LinkingSessionStarted] = []
        for doc in await started_sessions_cursor.to_list(length=100):
            link = LinkingSessionStarted.model_validate(doc)
            linking_sessions_started.append(link)

        return linking_sessions_started

    async def get_expired_completed_sessions(
        self, now: int
    ) -> List[LinkingSessionComplete]:
        completed_sessions_cursor = self.db.linking_sessions_completed.find(
            {"expires_at": {"$lte": now}}
        )
        linking_sessions_completed: List[LinkingSessionComplete] = []
        for doc in await completed_sessions_cursor.to_list(length=100):
            link = LinkingSessionComplete.model_validate(doc)
            linking_sessions_completed.append(link)
        return linking_sessions_completed

    async def get_expired_sessions(self, now: int) -> ExpiredSessions:
        linking_sessions_initial = await self.get_expired_initial_sessions(now)
        linking_sessions_started = await self.get_expired_started_sessions(now)
        linking_sessions_completed = await self.get_expired_completed_sessions(now)

        return ExpiredSessions(
            initial_sessions=linking_sessions_initial,
            started_sessions=linking_sessions_started,
            completed_sessions=linking_sessions_completed,
        )

    async def get_linking_session_initial(
        self, session_id: str
    ) -> LinkingSessionInitial | None:
        session = await self.db.linking_sessions_initial.find_one(
            {"session_id": session_id}
        )

        if session is None:
            return None
        else:
            # session["kind"] = "initial"
            return LinkingSessionInitial.model_validate(session)

    async def get_linking_session_started(
        self, session_id: str
    ) -> LinkingSessionStarted | None:
        session = await self.db.linking_sessions_started.find_one(
            {"session_id": session_id}
        )
        if session is None:
            return None
        else:
            return LinkingSessionStarted.model_validate(session)

    async def get_linking_session_completed(
        self, session_id: str
    ) -> LinkingSessionComplete | None:
        session = await self.db.linking_sessions_completed.find_one(
            {"session_id": session_id}
        )

        if session is None:
            return None
        else:
            # session["kind"] = "complete"
            return LinkingSessionComplete.model_validate(session)

    async def get_linking_sessions_completed(self) -> List[LinkingSessionComplete]:
        cursor = self.db.linking_sessions_completed.find({})

        linking_sessions: List[LinkingSessionComplete] = []

        for doc in await cursor.to_list(length=100):
            link = LinkingSessionComplete.model_validate(doc)
            linking_sessions.append(link)

        return linking_sessions

    async def get_linking_sessions_started(self) -> List[LinkingSessionStarted]:
        cursor = self.db.linking_sessions_started.find({})

        linking_sessions: List[LinkingSessionStarted] = []

        for doc in await cursor.to_list(length=100):
            link = LinkingSessionStarted.model_validate(doc)
            linking_sessions.append(link)

        return linking_sessions

    async def get_linking_sessions_initial(self) -> List[LinkingSessionInitial]:
        cursor = self.db.linking_sessions_initial.find({})

        linking_sessions: List[LinkingSessionInitial] = []

        for doc in await cursor.to_list(length=100):
            link = LinkingSessionInitial.model_validate(doc)
            linking_sessions.append(link)

        return linking_sessions

    async def update_linking_session_to_started(
        self,
        session_id: str,
        return_link: str | None,
        skip_prompt: bool,
        ui_options: str,
    ) -> None:
        async with await self.client.start_session() as session:
            # Get the initial linking session.
            linking_session = await self.db.linking_sessions_initial.find_one(
                {"session_id": session_id}, session=session
            )

            if linking_session is None:
                raise NotFoundError("Linking session not found")

            updated_linking_session = dict(linking_session)

            updated_linking_session["return_link"] = return_link
            updated_linking_session["skip_prompt"] = skip_prompt
            updated_linking_session["ui_options"] = ui_options

            await self.db.linking_sessions_started.insert_one(
                updated_linking_session, session=session
            )

            await self.db.linking_sessions_initial.delete_one(
                {"session_id": session_id}, session=session
            )

    async def update_linking_session_to_finished(
        self, session_id: str, orcid_auth: ORCIDAuth
    ) -> None:
        async with await self.client.start_session() as session:
            # Get the initial linking session.
            linking_session = await self.db.linking_sessions_started.find_one(
                {"session_id": session_id}, session=session
            )

            if linking_session is None:
                raise NotFoundError("Linking session not found")
                # raise exceptions.ServiceErrorY(
                #     error=errors.ERRORS.not_found,
                #     message="Linking session not found",
                # )

            updated_linking_session = dict(linking_session)

            updated_linking_session["orcid_auth"] = orcid_auth.model_dump()

            await self.db.linking_sessions_completed.insert_one(
                updated_linking_session, session=session
            )

            await self.db.linking_sessions_started.delete_one(
                {"session_id": session_id}, session=session
            )

    async def reset_database(self) -> None:
        await self.db.links.drop()
        await self.db.linking_sessions_initial.drop()
        await self.db.linking_sessions_started.drop()
        await self.db.linking_sessions_completed.drop()
        await self.db.description.drop()

    async def get_stats(self) -> StatsRecord:
        now = posix_time_millis()

        day = 24 * 60 * 60 * 1000

        links_last_24_hours = await self.db.links.count_documents(
            {"created_at": {"$gte": now - day}}
        )
        links_last_7_days = await self.db.links.count_documents(
            {"created_at": {"$gte": now - 7 * day}}
        )
        links_last_30_days = await self.db.links.count_documents(
            {"created_at": {"$gte": now - 30 * day}}
        )
        links_all_time = await self.db.links.count_documents({})

        linking_sessions_initial_active = (
            await self.db.linking_sessions_initial.count_documents(
                {"expires_at": {"$gt": now}}
            )
        )

        linking_sessions_initial_expired = (
            await self.db.linking_sessions_initial.count_documents(
                {"expires_at": {"$lte": now}}
            )
        )

        linking_sessions_started_active = (
            await self.db.linking_sessions_started.count_documents(
                {"expires_at": {"$gt": now}}
            )
        )

        linking_sessions_started_expired = (
            await self.db.linking_sessions_started.count_documents(
                {"expires_at": {"$lte": now}}
            )
        )

        linking_sessions_completed_active = (
            await self.db.linking_sessions_completed.count_documents(
                {"expires_at": {"$gt": now}}
            )
        )

        linking_sessions_completed_expired = (
            await self.db.linking_sessions_completed.count_documents(
                {"expires_at": {"$lte": now}}
            )
        )

        return StatsRecord(
            links=LinkStats(
                last_24_hours=links_last_24_hours,
                last_7_days=links_last_7_days,
                last_30_days=links_last_30_days,
                all_time=links_all_time,
            ),
            linking_sessions_initial=LinkSessionStats(
                active=linking_sessions_initial_active,
                expired=linking_sessions_initial_expired,
            ),
            linking_sessions_started=LinkSessionStats(
                active=linking_sessions_started_active,
                expired=linking_sessions_started_expired,
            ),
            linking_sessions_completed=LinkSessionStats(
                active=linking_sessions_completed_active,
                expired=linking_sessions_completed_expired,
            ),
        )
