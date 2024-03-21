from typing import Dict, List

from orcidlink import model
from orcidlink.jsonrpc.errors import ORCIDProfileNamePrivate
from orcidlink.lib.service_clients import orcid_api
from orcidlink.lib.service_clients.orcid_common import ORCIDStringValue
from orcidlink.model import (
    CitationType,
    ContributorRole,
    ContributorRoleValue,
    ExternalId,
    ExternalIdType,
    ORCIDBiographyFields,
    ORCIDContributorSelf,
    ORCIDEmailFields,
    ORCIDFieldGroup,
    ORCIDNameFields,
    RelationshipType,
    WorkType,
)


def orcid_date_to_string_date(orcid_date: orcid_api.Date) -> str:
    # def pad(s: str) -> str:
    #     return s.lstrip('0').rjust(2, '0')

    def nopad(s: str) -> str:
        return s.lstrip("0")

    year = orcid_date.year.value
    if orcid_date.month is not None:
        month = orcid_date.month.value
    else:
        month = None

    if orcid_date.day is not None:
        day = orcid_date.day.value
    else:
        day = None

    if month is not None:
        if day is not None:
            return f"{year}/{nopad(month)}/{nopad(day)}"
        else:
            return f"{year}/{nopad(month)}"
    else:
        return f"{year}"


def transform_external_id(external_id: orcid_api.ExternalId) -> model.ExternalId:
    """
    Transforms an ORCID external id to an orcidlink model external id.

    As with many of these transformations, it simplifies the structure. The ORCID
    structures often have fields we don't need, overly verbose property names, and
    "value" sub-properties.
    """
    return model.ExternalId(
        type=ExternalIdType(external_id.external_id_type),
        value=external_id.external_id_value,
        url=external_id.external_id_url.value,
        relationship=RelationshipType(external_id.external_id_relationship),
    )


def transform_work_summary(
    work_summary: orcid_api.WorkSummary,
) -> model.WorkSummary:
    """
    Transforms an ORCID work record into a simpler work record as emitted by
    the api.
    """

    # TODO: should also get the source app id
    external_ids: List[ExternalId] = []
    self_dois: List[str] = []
    # for external_id in work_summary.external_ids.external_id:
    #     if (
    #             external_id.external_id_type == "doi"
    #             and external_id.external_id_relationship == "self"
    #     ):
    #         doi = external_id.external_id_value
    #         continue
    #     external_ids.append(transform_external_id(external_id))

    # TODO: this is a hack, because there are old development records w/o a doi.
    # if doi is None:
    #     doi = ""

    for external_id in work_summary.external_ids.external_id:
        if (
            external_id.external_id_type == "doi"
            and external_id.external_id_relationship == "self"
        ):
            self_dois.append(external_id.external_id_value)
        else:
            external_ids.append(transform_external_id(external_id))

    if len(self_dois) == 0:
        raise ValueError(
            'there must be one external id of type "doi" and relationship "self"'
        )
    if len(self_dois) > 1:
        raise ValueError(
            'there may be only one external id of type "doi" and relationship "self"'
        )

    doi = self_dois[0]

    journal = (
        None if work_summary.journal_title is None else work_summary.journal_title.value
    )

    return model.WorkSummary(
        putCode=work_summary.put_code,
        createdAt=work_summary.created_date.value,
        updatedAt=(
            work_summary.last_modified_date.value
            if work_summary.last_modified_date is not None
            else None
        ),
        source=(
            work_summary.source.source_name.value
            if work_summary.source.source_name is not None
            else None
        ),
        title=work_summary.title.title.value,
        journal=journal,
        date=orcid_date_to_string_date(work_summary.publication_date),
        workType=WorkType(work_summary.type),
        url=work_summary.url.value,
        doi=doi,
        externalIds=external_ids,
    )


def transform_work(
    profile: orcid_api.ORCIDProfile, raw_work: orcid_api.Work
) -> model.Work:
    """
    Transforms an ORCID work record into a simpler work record as emitted by
    the api.

    Note that although ORCID allows for some fields to be optional, for those that
    we control we require that some of those be  populated.
    """
    put_code = raw_work.put_code
    created_at = raw_work.created_date.value
    if raw_work.last_modified_date is not None:
        updated_at = raw_work.last_modified_date.value
    else:
        updated_at = None

    # TODO: should also get the source app id
    source = (
        raw_work.source.source_name.value
        if raw_work.source.source_name is not None
        else None
    )
    date = orcid_date_to_string_date(raw_work.publication_date)
    title = raw_work.title.title.value
    journal = (
        raw_work.journal_title.value if raw_work.journal_title is not None else None
    )
    work_type = raw_work.type
    url = raw_work.url.value

    if journal is None:
        raise ValueError('the "journal" field may not be empty')

    # Now for external ids
    external_ids: List[ExternalId] = []
    self_dois: List[str] = []
    for external_id in raw_work.external_ids.external_id:
        if (
            external_id.external_id_type == "doi"
            and external_id.external_id_relationship == "self"
        ):
            self_dois.append(external_id.external_id_value)
        else:
            external_ids.append(transform_external_id(external_id))

    if len(self_dois) == 0:
        raise ValueError(
            'there must be one external id of type "doi" and relationship "self"'
        )
    if len(self_dois) > 1:
        raise ValueError(
            'there may be only one external id of type "doi" and relationship "self"'
        )

    doi = self_dois[0]

    # Self Contributor

    self_roles: List[ContributorRole] = []
    for contributor in raw_work.contributors.contributor:
        if contributor.contributor_orcid.path == profile.orcid_identifier.path:
            # if contributor.contributor_attributes is not None:
            self_roles.append(
                ContributorRole(
                    role=ContributorRoleValue(
                        contributor.contributor_attributes.contributor_role
                    )
                )
            )

    if profile.person.name is None:
        raise ORCIDProfileNamePrivate("Your ORCID Profile has your name set as private")
    elif profile.person.name.credit_name is not None:
        name = profile.person.name.credit_name
    elif profile.person.name.family_name is None:
        name = ORCIDStringValue(value=f"{profile.person.name.given_names.value}")
    else:
        name = ORCIDStringValue(
            value=(
                f"{profile.person.name.given_names.value} "
                f"{profile.person.name.family_name.value}"
            )
        )

    self_contributor = ORCIDContributorSelf(
        name=name.value, orcidId=profile.orcid_identifier.path, roles=self_roles
    )

    if raw_work.citation is None:
        raise ValueError('the "citation" field may not be empty')

    citation = model.ORCIDCitation(
        type=CitationType(raw_work.citation.citation_type),
        value=raw_work.citation.citation_value,
    )

    # A note on how we deal with building a list of contributors.
    # The ORCID data structure has one list item per contributor and role
    # Therefore there are N entries per contributor with N roles.
    # In order to generate one contributor entry with N roles, we
    # use a dict of contributor "credit_name".

    contributors_map: Dict[str, model.ORCIDContributor] = {}
    for contributor in raw_work.contributors.contributor:
        # The "path" attribute is the orcid id.
        # We omit the orcid profile owner from the list of
        # "other contributors"
        if contributor.contributor_orcid.path == self_contributor.orcidId:
            continue

        # We use the "credit_name" as the key for contributors.
        # This is not perfect, but believe that is all we have, other than
        # orcid id, which is not required
        if contributor.credit_name.value not in contributors_map:
            # If we have not encountered this contributor yet, we create
            # an entry in dict for them with this one role.
            role = contributor.contributor_attributes.contributor_role
            new_contributor = model.ORCIDContributor(
                name=contributor.credit_name.value,
                roles=[ContributorRole(role=ContributorRoleValue(role))],
                orcidId=contributor.contributor_orcid.path,
            )
            # We optionally set the orcidId.
            if contributor.contributor_orcid.path is not None:
                new_contributor.orcidId = contributor.contributor_orcid.path

            contributors_map[contributor.credit_name.value] = new_contributor
        else:
            # And if we have seen this contributor before, we simply
            # append the role for this entry.
            role = contributor.contributor_attributes.contributor_role
            contributors_map[contributor.credit_name.value].roles.append(
                ContributorRole(role=ContributorRoleValue(role))
            )

    other_contributors = list(contributors_map.values())

    short_description = raw_work.short_description

    if short_description is None:
        raise ValueError('the "short_description" field may not be empty')

    orcid_work = model.Work(
        putCode=put_code,
        createdAt=created_at,
        updatedAt=updated_at,
        source=source,
        title=title,
        journal=journal,
        date=date,
        workType=WorkType(work_type),
        url=url,
        doi=doi,
        externalIds=external_ids,
        shortDescription=short_description,
        citation=citation,
        selfContributor=self_contributor,
        otherContributors=other_contributors,
    )

    return orcid_work


# class ORCIDDateValue(TypedDict):
#     value: str


def transform_affilations(
    affiliation_group: (
        orcid_api.ORCIDAffiliationGroup | List[orcid_api.ORCIDAffiliationGroup]
    ),
) -> List[model.ORCIDAffiliation]:
    def coerce_to_list(
        from_orcid: (
            orcid_api.ORCIDAffiliationGroup | List[orcid_api.ORCIDAffiliationGroup]
        ),
    ) -> List[orcid_api.ORCIDAffiliationGroup]:
        if isinstance(from_orcid, orcid_api.ORCIDAffiliationGroup):
            return [from_orcid]
        else:
            return from_orcid

    aff_group = coerce_to_list(affiliation_group)

    affiliations: List[model.ORCIDAffiliation] = []
    for affiliation in aff_group:
        #
        # For some reason there is a list of summaries here, but I don't
        # see such a structure in the XML, so just take the first element.
        #
        employment_summary = affiliation.summaries[0].employment_summary
        name = employment_summary.organization.name
        role = employment_summary.role_title
        start_year = employment_summary.start_date.year.value
        if employment_summary.end_date is not None:
            end_year = employment_summary.end_date.year.value
        else:
            end_year = None

        affiliations.append(
            model.ORCIDAffiliation(
                name=name, role=role, startYear=start_year, endYear=end_year
            )
        )
    return affiliations


def orcid_profile(profile_raw: orcid_api.ORCIDProfile) -> model.ORCIDProfile:
    # Organizations / Employment!

    affiliation_group = profile_raw.activities_summary.employments.affiliation_group
    transform_affilations(affiliation_group)

    #
    # Publications
    # works = []
    #
    # activity_works = profile_raw.activities_summary.works.group
    # for work in activity_works:
    #     work_summary = work.work_summary[0]
    #     # get_raw_prop(work, ["work-summary", 0], None)
    #     # only include works that we created.
    #     # TODO: the source needs to be configurable
    #     if work_summary.source != "KBase CI":
    #         continue
    #     works.append(transform_work_summary(work_summary))

    # if profile_raw.person.name is not None and profile_raw.person.name.credit_name
    # is not None:
    #     creditName = profile_raw.person.name.credit_name.value
    # else:
    #     creditName = None

    # bio = None
    # if profile_raw.person.biography is not None:
    #     bio = profile_raw.person.biography.content

    if profile_raw.person.name is None:
        name_group = ORCIDFieldGroup[ORCIDNameFields](private=True, fields=None)
    else:
        name_group = ORCIDFieldGroup[ORCIDNameFields](
            private=False,
            fields=ORCIDNameFields(
                firstName=profile_raw.person.name.given_names.value,
                lastName=(
                    profile_raw.person.name.family_name.value
                    if profile_raw.person.name.family_name is not None
                    else None
                ),
                creditName=(
                    profile_raw.person.name.credit_name.value
                    if profile_raw.person.name.credit_name is not None
                    else None
                ),
            ),
        )

    if profile_raw.person.biography is None:
        biography_group = ORCIDFieldGroup[ORCIDBiographyFields](
            private=True, fields=None
        )
    else:
        biography_group = ORCIDFieldGroup[ORCIDBiographyFields](
            private=False,
            fields=ORCIDBiographyFields(bio=profile_raw.person.biography.content),
        )

    if profile_raw.person.emails is None:
        email_group = ORCIDFieldGroup[ORCIDEmailFields](private=True, fields=None)
    else:
        email_addresses: List[str] = []
        for email in profile_raw.person.emails.email:
            email_addresses.append(email.email)
        email_group = ORCIDFieldGroup[ORCIDEmailFields](
            private=False, fields=ORCIDEmailFields(emailAddresses=email_addresses)
        )

    return model.ORCIDProfile(
        orcidId=profile_raw.orcid_identifier.path,
        nameGroup=name_group,
        biographyGroup=biography_group,
        # works=works,
        # emailAddresses=email_addresses,
        emailGroup=email_group,
        # what is missing?
        # websites + social links, keywords, countries
        employment=transform_affilations(
            profile_raw.activities_summary.employments.affiliation_group
        ),
    )
