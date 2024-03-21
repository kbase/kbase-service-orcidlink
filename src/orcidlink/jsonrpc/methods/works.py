import json
from typing import List

import aiohttp

from orcidlink import process
from orcidlink.jsonrpc.errors import NotFoundError, UpstreamError
from orcidlink.lib.service_clients import orcid_api
from orcidlink.lib.service_clients.orcid_common import ORCIDStringValue
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.model import NewWork, ORCIDWorkGroup, Work, WorkUpdate
from orcidlink.runtime import config
from orcidlink.translators import to_orcid, to_service


async def get_works(username: str) -> List[ORCIDWorkGroup]:
    link_record = await process.link_record_for_user(username)
    if link_record is None:
        raise NotFoundError("Link Record Not Found")

    token = link_record.orcid_auth.access_token
    orcid_id = link_record.orcid_auth.orcid

    orcid_works = await orcid_api.orcid_api(token).get_works(orcid_id)

    result: List[ORCIDWorkGroup] = []
    for group in orcid_works.group:
        result.append(
            ORCIDWorkGroup(
                updatedAt=group.last_modified_date.value,
                externalIds=[
                    to_service.transform_external_id(external_id)
                    for external_id in group.external_ids.external_id
                ],
                works=[
                    to_service.transform_work_summary(work_summary)
                    # TODO: Need to make the KBase source configurable, as it will be
                    # different, between, say, CI and prod, or at least development and
                    # prod.
                    for work_summary in group.work_summary
                    # TODO: replace with source_client_id and compare to the client id
                    # in the config.
                    if work_summary.source.source_name is not None
                    and work_summary.source.source_name.value == "KBase CI"
                ],
            )
        )

    return result


class GetWorkResult(ServiceBaseModel):
    work: Work


async def get_work(username: str, put_code: int) -> GetWorkResult:
    link_record = await process.link_record_for_user(username)
    if link_record is None:
        raise NotFoundError("ORCID Link Not Found")

    token = link_record.orcid_auth.access_token
    orcid_id = link_record.orcid_auth.orcid

    # try:
    raw_work = await orcid_api.orcid_api(token).get_work(orcid_id, put_code)
    profile = await orcid_api.orcid_api(token).get_profile(orcid_id)
    return GetWorkResult(work=to_service.transform_work(profile, raw_work.bulk[0].work))


class CreateWorkResult(ServiceBaseModel):
    work: Work


async def create_work(username: str, new_work: NewWork) -> CreateWorkResult:
    link_record = await process.link_record_for_user(username)
    if link_record is None:
        raise NotFoundError("ORCID Profile Not Found")

    token = link_record.orcid_auth.access_token
    orcid_id = link_record.orcid_auth.orcid

    #
    # Create initial work record
    #

    external_ids: List[orcid_api.ExternalId] = [
        orcid_api.ExternalId(
            external_id_type="doi",
            external_id_value=new_work.doi,
            external_id_normalized=None,
            # TODO: doi url should be configurable
            external_id_url=ORCIDStringValue(value=f"https://doi.org/{new_work.doi}"),
            external_id_relationship="self",
        )
    ]

    # external_ids: List[orcid_api.ORCIDExternalId] = []
    # if new_work.externalIds is not None:
    for _, externalId in enumerate(new_work.externalIds):
        external_ids.append(
            orcid_api.ExternalId(
                external_id_type=externalId.type,
                external_id_value=externalId.value,
                external_id_url=ORCIDStringValue(value=externalId.url),
                external_id_relationship=externalId.relationship,
            )
        )

    citation = orcid_api.Citation(
        citation_type=new_work.citation.type,
        citation_value=new_work.citation.value,
    )

    contributors: List[orcid_api.Contributor] = []

    self_contributors = to_orcid.transform_contributor_self(new_work.selfContributor)
    contributors.extend(self_contributors)

    contributors.extend(to_orcid.transform_contributors(new_work.otherContributors))

    work_record = orcid_api.NewWork(
        type=new_work.workType,
        title=orcid_api.Title(title=ORCIDStringValue(value=new_work.title)),
        journal_title=ORCIDStringValue(value=new_work.journal),
        url=ORCIDStringValue(value=new_work.url),
        external_ids=orcid_api.ExternalIds(external_id=external_ids),
        publication_date=to_orcid.parse_date(new_work.date),
        short_description=new_work.shortDescription,
        citation=citation,
        contributors=orcid_api.ContributorWrapper(contributor=contributors),
    )

    url = orcid_api.orcid_api_url(f"{orcid_id}/works")
    header = {
        "Accept": "application/vnd.orcid+json",
        "Content-Type": "application/vnd.orcid+json",
        "Authorization": f"Bearer {token}",
    }

    # Note that we use the "bulk" endpoint because it nicely returns the newly created
    # work record. This both saves a trip and is more explicit than the singular
    # endpoint POST /work, which returns 201 and a location for the new work record,
    # which we would need to parse to extract the put code.
    #
    # TODO: also this endpoint and probably many others return a 200 response with error
    # data.
    content = orcid_api.CreateWorkInput(
        bulk=(orcid_api.NewWorkWrapper(work=work_record),)
    )

    # TODO: propagate everywhere. Or, perhaps better,
    # wrap this common use case into a function or class.
    timeout = config().request_timeout
    try:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url,
                timeout=timeout,
                headers=header,
                data=json.dumps(content.model_dump(by_alias=True)),
            ) as response:
                result = await response.json()
                work_record2 = orcid_api.GetWorkResult.model_validate(result)
                # TODO: handle errors here; they are not always
                profile = await orcid_api.orcid_api(token).get_profile(orcid_id)
                new_work_record = to_service.transform_work(
                    profile, work_record2.bulk[0].work
                )
                return CreateWorkResult(work=new_work_record)
    except aiohttp.ClientError:
        # TODO: richer error here.
        raise UpstreamError(
            "An error was encountered saving the work record",
            # data={
            #     "description": str(ex),
            # },
        )


class SaveWorkResult(ServiceBaseModel):
    work: Work


async def save_work(username: str, work_update: WorkUpdate) -> SaveWorkResult:
    link_record = await process.link_record_for_user(username)
    if link_record is None:
        raise NotFoundError("ORCID Profile Not Found")

    token = link_record.orcid_auth.access_token
    orcid_id = link_record.orcid_auth.orcid

    put_code = work_update.putCode

    work_record_updated = to_orcid.translate_work_update(work_update)

    # TODO: check this
    raw_work_record = await orcid_api.orcid_api(token).save_work(
        orcid_id, put_code, work_record_updated
    )

    profile = await orcid_api.orcid_api(token).get_profile(orcid_id)
    return SaveWorkResult(work=to_service.transform_work(profile, raw_work_record))


async def delete_work(username: str, put_code: int) -> None:
    link_record = await process.link_record_for_user(username)
    if link_record is None:
        raise NotFoundError("ORCID Profile Not Found")

    token = link_record.orcid_auth.access_token
    orcid_id = link_record.orcid_auth.orcid

    header = {
        "Accept": "application/vnd.orcid+json",
        "Authorization": f"Bearer {token}",
    }
    url = orcid_api.orcid_api_url(f"{orcid_id}/work/{put_code}")

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=header) as response:
            if response.status == 204:
                return None

            # TODO: richer error
            raise UpstreamError(
                "The ORCID API reported an error fo this request, see 'data' for cause",
                # data={"upstreamError": await response.json()},
            )
