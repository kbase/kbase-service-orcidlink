from typing import List

from orcidlink import model
from orcidlink.lib.service_clients import orcid_api
from orcidlink.lib.service_clients.orcid_common import ORCIDStringValue


def parse_date(date_string: str) -> orcid_api.Date:
    date_parts = date_string.split("/")
    if len(date_parts) == 1:
        return orcid_api.Date(year=ORCIDStringValue(value=date_parts[0]))
    elif len(date_parts) == 2:
        return orcid_api.Date(
            year=ORCIDStringValue(value=date_parts[0]),
            month=ORCIDStringValue(value=date_parts[1].rjust(2, "0")),
        )
    elif len(date_parts) == 3:
        return orcid_api.Date(
            year=ORCIDStringValue(value=date_parts[0]),
            month=ORCIDStringValue(value=date_parts[1].rjust(2, "0")),
            day=ORCIDStringValue(value=date_parts[2].rjust(2, "0")),
        )
    else:
        raise ValueError(
            f"Date must have 1-3 parts; has {len(date_parts)}: {date_string}"
        )


def transform_contributor_self(
    contributor_update: model.ORCIDContributorSelf,
) -> List[orcid_api.Contributor]:
    """
    Transforms a model Contributor to an orcid_api compatible
    contributor.

    This transformation is a bit strange, as ORCID has one contributor
    record per role. So one contributor with multiple roles is stored
    not as one contributor record with an array of roles, but rather
    as multiple contributor records with one per role!
    """
    contributor_records: List[orcid_api.Contributor] = []
    for role in contributor_update.roles:
        contributor_records.append(
            orcid_api.Contributor(
                contributor_orcid=orcid_api.ContributorORCID(
                    path=contributor_update.orcidId, uri=None, host=None
                ),
                credit_name=ORCIDStringValue(value=contributor_update.name),
                # seems unused - no way to access it in the ORCID ui
                contributor_email=None,
                contributor_attributes=orcid_api.ContributorAttributes(
                    # TODO: try removing below
                    contributor_sequence=None,
                    contributor_role=role.role,
                ),
            )
        )
    return contributor_records


def transform_contributor(
    contributor_update: model.ORCIDContributor,
) -> List[orcid_api.Contributor]:
    """
    Transforms a model Contributor to an orcid_api compatible
    contributor.

    This transformation is a bit strange, as ORCID has one contributor
    record per role. So one contributor with multiple roles is stored
    not as one contributor record with an array of roles, but rather
    as multiple contributor records with one per role!
    """
    contributor_records: List[orcid_api.Contributor] = []
    for role in contributor_update.roles:
        contributor = orcid_api.Contributor(
            credit_name=ORCIDStringValue(value=contributor_update.name),
            # seems unused - no way to access it in the ORCID ui, and we don't need to
            # collect it afaik.
            contributor_email=None,
            contributor_attributes=orcid_api.ContributorAttributes(
                contributor_sequence=None, contributor_role=role.role
            ),
            contributor_orcid=orcid_api.ContributorORCID(
                path=contributor_update.orcidId, uri=None, host=None
            ),
        )
        # if contributor_update.orcidId is not None:
        # contributor.contributor_orcid = orcid_api.ContributorORCID(
        #     uri=contributor_update.orcidId,
        #     path=None,
        #     host=None
        # )
        contributor_records.append(contributor)
    return contributor_records


def transform_contributors(
    contributors_update: List[model.ORCIDContributor],
) -> List[orcid_api.Contributor]:
    all_contributors: List[orcid_api.Contributor] = []
    for contributor in contributors_update:
        contributors = transform_contributor(contributor)
        all_contributors.extend(contributors)
    return all_contributors


def transform_contributors_self(
    contributors_update: List[model.ORCIDContributorSelf],
) -> List[orcid_api.Contributor]:
    all_contributors: List[orcid_api.Contributor] = []
    for contributor in contributors_update:
        contributors = transform_contributor_self(contributor)
        all_contributors.extend(contributors)
    return all_contributors


# TODO: return should be class
def translate_work_update(work_update: model.WorkUpdate) -> orcid_api.WorkUpdate:
    external_ids: List[orcid_api.ExternalId] = [
        orcid_api.ExternalId(
            external_id_type="doi",
            external_id_value=work_update.doi,
            external_id_normalized=None,
            # TODO: doi url should be configurable
            external_id_url=ORCIDStringValue(
                value=f"https://doi.org/{work_update.doi}"
            ),
            external_id_relationship="self",
        )
    ]
    for _, externalId in enumerate(work_update.externalIds):
        external_ids.append(
            orcid_api.ExternalId(
                external_id_type=externalId.type,
                external_id_value=externalId.value,
                external_id_normalized=None,
                external_id_url=ORCIDStringValue(value=externalId.url),
                external_id_relationship=externalId.relationship,
            )
        )

    citation = orcid_api.Citation(
        citation_type=work_update.citation.type,
        citation_value=work_update.citation.value,
    )
    # work_record.short_description = work_update.shortDescription

    contributors: List[orcid_api.Contributor] = []

    self_contributors = transform_contributor_self(work_update.selfContributor)
    contributors.extend(self_contributors)

    contributors.extend(transform_contributors(work_update.otherContributors))

    return orcid_api.WorkUpdate(
        put_code=work_update.putCode,
        type=work_update.workType,
        title=orcid_api.Title(title=ORCIDStringValue(value=work_update.title)),
        journal_title=ORCIDStringValue(value=work_update.journal),
        url=ORCIDStringValue(value=work_update.url),
        publication_date=orcid_api.Date.model_validate(parse_date(work_update.date)),
        external_ids=orcid_api.ExternalIds(external_id=external_ids),
        short_description=work_update.shortDescription,
        citation=citation,
        contributors=orcid_api.ContributorWrapper(contributor=contributors),
    )
