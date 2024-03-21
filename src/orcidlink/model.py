"""
Contains the data model for the application

Most application types used by router implementation should be located here. This
essentially represents the data model for the application. This insulates us from
the vagaries of the upstream APIs, and provides a consistent system of types,
naming conventions, etc.

All types inherit from pydantic's BaseModel, meaning that they will have bidirectional
JSON support, auto-documentation, the opportunity for more detailed schemas and
documentation.

"""

from enum import Enum
from typing import Generic, List, Optional, TypeVar, Union

from pydantic import Field

from orcidlink.lib.type import ServiceBaseModel


class SimpleSuccess(ServiceBaseModel):
    ok: bool = Field(...)


#
# ENUMS
#


# This is how we do the domain for a field.
# We should document, with each type, where and how
# we get the values.
# Since we probably need to provide these values for UI usage in a dropdown or
# similar control, we need to keep these in data format too, and located
# in /data or elsewhere.
# Extracted from the documentation in https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L253
# Could not find an actual data source.
# Local values located in /data/citation-type.json
class CitationType(str, Enum):
    bibtex = "bibtex"
    formatted_apa = "formatted-apa"
    formatted_chicago = "formatted-chicago"
    formatted_harvard = "formatted-harvard"
    formatted_ieee = "formatted-ieee"
    formatted_mla = "formatted-mla"
    formatted_vancouver = "formatted-vancouver"
    formatted_unspecified = "formatted-unspecified"
    ris = "ris"


class RelationshipType(str, Enum):
    self = "self"
    part_of = "part-of"
    version_of = "version-of"
    funded_by = "funded-by"


class ContributorRoleValue(str, Enum):
    conceptualization = "http://credit.niso.org/contributor-roles/conceptualization/"
    data_curation = "http://credit.niso.org/contributor-roles/data-curation/"
    formal_analysis = "http://credit.niso.org/contributor-roles/formal-analysis/"
    funding_acquisition = (
        "http://credit.niso.org/contributor-roles/funding-acquisition/"
    )
    investigation = "http://credit.niso.org/contributor-roles/investigation/"
    methodology = "http://credit.niso.org/contributor-roles/methodology/"
    project_administration = (
        "http://credit.niso.org/contributor-roles/project-administration/"
    )
    resources = "http://credit.niso.org/contributor-roles/resources/"
    software = "http://credit.niso.org/contributor-roles/software/"
    supervision = "http://credit.niso.org/contributor-roles/supervision/"
    validation = "http://credit.niso.org/contributor-roles/validation/"
    visualization = "http://credit.niso.org/contributor-roles/visualization/"
    writing_original_draft = (
        "http://credit.niso.org/contributor-roles/writing-original-draft/"
    )
    writing_review_editing = (
        "http://credit.niso.org/contributor-roles/writing-review-editing/"
    )


class ExternalIdType(str, Enum):
    agr = "agr"
    ark = "ark"
    arxiv = "arxiv"
    asin = "asin"
    asin_tld = "asin-tld"
    authenticusid = "authenticusid"
    bibcode = "bibcode"
    cba = "cba"
    cienciaiul = "cienciaiul"
    cit = "cit"
    cstr = "cstr"
    ctx = "ctx"
    dnb = "dnb"
    doi = "doi"
    eid = "eid"
    emdb = "emdb"
    empiar = "empiar"
    ethos = "ethos"
    grant_number = "grant_number"
    hal = "hal"
    handle = "handle"
    hir = "hir"
    isbn = "isbn"
    ismn = "ismn"
    issn = "issn"
    jfm = "jfm"
    jstor = "jstor"
    k10plus = "k10plus"
    kuid = "kuid"
    lccn = "lccn"
    lensid = "lensid"
    mr = "mr"
    oclc = "oclc"
    ol = "ol"
    osti = "osti"
    other_id = "other-id"
    pat = "pat"
    pdb = "pdb"
    pmc = "pmc"
    pmid = "pmid"
    ppr = "ppr"
    proposal_id = "proposal-id"
    rfc = "rfc"
    rrid = "rrid"
    source_work_id = "source-work-id"
    ssrn = "ssrn"
    uri = "uri"
    urn = "urn"
    wosuid = "wosuid"
    zbl = "zbl"


class ExternalId(ServiceBaseModel):
    """
    See: https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L1025
    """

    type: ExternalIdType = Field(
        title="External Id Type",
        description="The type of an external identifier",
        # custom
        json_schema_extra={
            "kbComment": "",
            "kbNotes": [
                "Supported external-id-type values can be found at https://pub.orcid.org/v2.0/identifiers",
                "Note that the above is an html table, although the page is simple, unstyled.",
                "From common.xsd: Must contain one or more charaters that are not a space, carriage return or linefeed",
                "Uses this regex as a rule to ensure this:  ",
                r"[\s\S]*[^\s\n\r]+[\s\S]*",
            ],
            "kbSourceName": "",
            "kbSourceType": "common:non-empty-string",
            "kbSourceTypeRef": "",
            "kbSourceValues": "https://pub.orcid.org/v2.0/identifiers",
            "kbUpstreamType": "xs:string",
            "kbUpstreamTypeRef": "https://www.w3.org/TR/xmlschema11-2/#string",
        },
    )
    value: str = Field(
        title="External Id Value",
        description="The value of an external identifier",
        # custom
        json_schema_extra={
            "kbComment": "",
            "kbNotes": ["Same generic 'non-empty-string' as above."],
            "kbSourceName": "",
            "kbSourceType": "common:non-empty-string",
            "kbSourceTypeRef": "",
            "kbSourceValues": "https://pub.orcid.org/v2.0/identifiers",
            "kbUpstreamType": "xs:string",
            "kbUpstreamTypeRef": "https://www.w3.org/TR/xmlschema11-2/#string",
        },
    )
    # Note that we skip ext external-id-normalized and external-id-normalized-error as
    # there is nothing we can clearly do with them. Actually, it is the type
    # "transient-non-empty-string" meaning that it is populated by ORCID as noted here:
    # https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L301
    url: str = Field(
        title="External Id URL",
        description="",
        # custom
        # kbComment="",
        # kbNotes=["See notes for other usages of anyURL"],
        # kbSourceName="work:url -> common:url ",
        # kbSourceType="common:url",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L353",
        # kbUpstreamType="xs:anyURI",
        # kbUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#anyURI",
    )
    relationship: RelationshipType = Field(
        title="External Id Relationship",
        description="",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Available values are located in common.xsd itself!",
        #     "along with a reference to a java class that applies 'other rules'"
        #     "see source ref url below",
        # ],
        # kbSourceName="relationship-type",
        # kbSourceType="common:external-id:external-id-url -> common:relationship-type",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L1010",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#string",
    )


class ORCIDAuth(ServiceBaseModel):
    access_token: str = Field(...)
    token_type: str = Field(...)
    refresh_token: str = Field(...)
    expires_in: int = Field(...)
    scope: str = Field(...)
    name: str = Field(...)
    orcid: str = Field(...)


class ORCIDAuthPublic(ServiceBaseModel):
    name: str = Field(...)
    scope: str = Field(...)
    expires_in: int = Field(...)
    orcid: str = Field(...)


class ORCIDAuthPublicNonOwner(ServiceBaseModel):
    name: str = Field(...)
    orcid: str = Field(...)


# Linking session

# Used when a session is initially created.
# It contains the state info needed in order to
# properly evaluate the linking session interactions in the
# absence of the original UI.
# E.g. cannot rely on having the auth cookie available, so we
# store it.


class LinkingSessionBase(ServiceBaseModel):
    session_id: str = Field(...)
    username: str = Field(...)
    created_at: int = Field(...)
    expires_at: int = Field(...)


class LinkingSessionInitial(LinkingSessionBase):
    # kind: Literal["initial"]
    pass


class LinkingSessionStarted(LinkingSessionBase):
    # kind: Literal["started"]
    return_link: str | None = Field(...)
    skip_prompt: bool = Field(...)
    ui_options: str = Field(...)


class LinkingSessionComplete(LinkingSessionBase):
    # kind: Literal["complete"]
    return_link: str | None = Field(...)
    skip_prompt: bool = Field(...)
    ui_options: str = Field(...)
    orcid_auth: ORCIDAuth = Field(...)


# LinkingSession = Annotated[
#     Union[LinkingSessionInitial, LinkingSessionStarted, LinkingSessionComplete],
#     Field(discriminator="kind"),
# ]


# TODO: maybe just a quick hack, but we use
# this concept of "public" vs "private" types.
# Public types are safe for exposing via the api.
class LinkingSessionCompletePublic(LinkingSessionBase):
    # kind: Literal["complete"]
    return_link: str | None = Field(...)
    skip_prompt: bool = Field(...)
    ui_options: str = Field(...)
    orcid_auth: ORCIDAuthPublic = Field(...)


# class LinkingSessionPublic(ServiceBaseModel):
#     __root__: Union[LinkingSessionInitial, LinkingSessionStarted,
#               LinkingSessionCompletePublic]


# LinkingSessionPublic = Annotated[
#     Union[LinkingSessionInitial, LinkingSessionStarted, LinkingSessionCompletePublic],
#     Field(discriminator="kind"),
# ]


class SessionInfo(ServiceBaseModel):
    session_id: str = Field(...)


# The Link itself


class LinkRecord(ServiceBaseModel):
    username: str = Field(...)
    created_at: int = Field(...)
    expires_at: int = Field(...)
    retires_at: int = Field(...)
    orcid_auth: ORCIDAuth = Field(...)


# TODO: actually, this isn't really public, just what we can send over the wire
# to the authorized user (owner of the link).
class LinkRecordPublic(ServiceBaseModel):
    username: str = Field(...)
    created_at: int = Field(...)
    expires_at: int = Field(...)
    retires_at: int = Field(...)
    orcid_auth: ORCIDAuthPublic = Field(...)


class LinkRecordPublicNonOwner(ServiceBaseModel):
    username: str = Field(...)
    orcid_auth: ORCIDAuthPublicNonOwner = Field(...)


class LinkingRecordShared(ServiceBaseModel):
    orcidId: str = Field(...)


# Config


class ServiceDescription(ServiceBaseModel):
    name: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=5, max_length=100)
    version: str = Field(min_length=5, max_length=50)
    language: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=50, max_length=4000)
    repoURL: str = Field(min_length=15, max_length=100)


# API


class ORCIDCitation(ServiceBaseModel):
    type: CitationType = Field(
        title="Type",
        description="The type (format) of the citation.",
        # custom
        # kbComment="",
        # kbNotes=["The available values are cited in work.xsd itself"],
        # kbSourceName="citation-type",
        # kbSourceType="work:citation -> citation-type -> work:citation-type",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L251",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    value: str = Field(
        title="Value",
        description="Formatted citation text.",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "A simple string with no constraints",
        #     "You would think it would be constrained to something large just ",
        #     "for sanity ",
        # ],
        # kbSourceName="",
        # kbSourceType="work:citation -> citation-value",
        # kbSourceTypeRef="",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )


# class ORCIDContributorORCIDInfo(ServiceBaseModel):
#     uri: str = Field(...)
#     path: str = Field(...)
#     # omitting host, seems never used


class ContributorRole(ServiceBaseModel):
    # TODO: add the sequence field so that the order is preserved
    role: ContributorRoleValue = Field(
        title="Role",
        description="The role performed by the collaborator or other contributor. ",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Interestingly this is called contributor-attributes in the orcid xsd",
        #     "The role itself is stored as a structure with a sequence (index) and the role itself.",
        #     "Note that this the available values consist of old and new ones.",
        #     "The new ones are all from credit.niso.org.",
        #     "Both are supported in their UI, but we should only support the new ones.",
        # ],
        # kbSourceName="contributor-role",
        # kbSourceType="work:contributor -> sequence of -> contributor-attributes -> work:contributor-attributes -> sequence of -> contributor-role -> common:contributor-role",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L191",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )


class ORCIDContributor(ServiceBaseModel):
    """
    Note that the orcidId is not required for the "regular" contributor.
    The "self contributor" described below, does, require it.
    """

    orcidId: Optional[str] = Field(
        default=None,
        title="ORCID Id",
        description="ORCID iD for the contributor - only add if you have collected an authenticated iD for the contributor",
        pattern="^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Although we simplify to just the orcid id string, at ORCID it is implemented",
        #     "as a more complex object. I won't explain that, just follow the link below to ",
        #     "see it in all it's glory...",
        # ],
        # kbSourceName="",
        # kbSourceType="work:contributor -> sequence of -> common:contributor-orcid -> common:orcid-id",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L421",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    name: str = Field(
        title="Name",
        description="The name to use for the researcher or contributor when credited or cited",
        max_length=150,
        # custom
        # kbComment="",
        # kbNotes=["a string of maximum length 150."],
        # kbSourceName="credit-name",
        # kbSourceType="work:contributor -> sequence of -> credit-name -> common:credit-name -> common:string-150",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L811",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    # omitting email, as it seems never used
    roles: List[ContributorRole] = Field(
        title="Roles",
        description="",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Interestingly this is called contributor-attributes in the orcid xsd",
        #     "The role itself is stored as a structure with a sequence (index) and the role itself.",
        #     "Note that this the available values consist of old and new ones.",
        #     "The new ones are all from credit.niso.org.",
        #     "Both are supported in their UI, but we should only support the new ones.",
        # ],
        # kbSourceName="contributor-role",
        # kbSourceType="work:contributor -> sequence of -> contributor-attributes -> work:contributor-attributes -> sequence of -> contributor-role -> common:contributor-role",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L191",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )


class ORCIDContributorSelf(ServiceBaseModel):
    orcidId: str = Field(
        title="ORCID Id",
        description=(
            "ORCID iD for the contributor - only add if you have collected an "
            "authenticated iD for the contributor"
        ),
        pattern="^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Although we simplify to just the orcid id string, at ORCID it is implemented",
        #     "as a more complex object. I won't explain that, just follow the link below to ",
        #     "see it in all it's glory...",
        # ],
        # kbSourceName="",
        # kbSourceType="work:contributor -> sequence of -> common:contributor-orcid -> common:orcid-id",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L421",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    name: str = Field(
        title="Name",
        description="The name to use for the researcher or contributor when credited or cited",
        max_length=150,
        # custom
        # kbComment="",
        # kbNotes=["a string of maximum length 150."],
        # kbSourceName="credit-name",
        # kbSourceType="work:contributor -> sequence of -> credit-name -> common:credit-name -> common:string-150",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L811",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    # omitting email, as it seems never used
    roles: List[ContributorRole] = Field(
        title="Roles",
        description="",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "Interestingly this is called contributor-attributes in the orcid xsd",
        #     "The role itself is stored as a structure with a sequence (index) and the role itself.",
        #     "Note that this the available values consist of old and new ones.",
        #     "The new ones are all from credit.niso.org.",
        #     "Both are supported in their UI, but we should only support the new ones.",
        # ],
        # kbSourceName="contributor-role",
        # kbSourceType="work:contributor -> sequence of -> contributor-attributes -> work:contributor-attributes -> sequence of -> contributor-role -> common:contributor-role",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L191",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )


# class ORCIDContributorSelf(ServiceBaseModel):
#     orcidId: str = Field(
#         title="ORCID Id",
#         description="ORCID iD for the contributor - only add if you have collected an authenticated iD for the contributor",
#         # custom
#         kbComment="",
#         kbNotes=[
#             "Although we simplify to just the orcid id string, at ORCID it is implemented",
#             "as a more complex object. I won't explain that, just follow the link below to ",
#             "see it in all it's glory...",
#         ],
#         kbSourceName="",
#         kbSourceType="work:contributor -> sequence of -> common:contributor-orcid -> common:orcid-id",
#         kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L421",
#         kbUpstreamType="",
#         kbUpstreamTypeRef="",
#     )
#     # orcidId: Optional[]
#     name: str = Field(
#         title="Name",
#         description="The name to use for the researcher or contributor when credited or cited",
#         max_length=150,
#         # custom
#         kbComment="",
#         kbNotes=["a string of maximum length 150."],
#         kbSourceName="credit-name",
#         kbSourceType="work:contributor -> sequence of -> credit-name -> common:credit-name -> common:string-150",
#         kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L811",
#         kbUpstreamType="xs:string",
#         kbUpstreamTypeRef="",
#     )
#     # omitting email, as it seems never used
#     roles: List[ContributorRole] = Field(
#         title="Roles",
#         description="",
#         # custom
#         kbComment="",
#         kbNotes=[
#             "Interestingly this is called contributor-attributes in the orcid xsd",
#             "The role itself is stored as a structure with a sequence (index) and the role itself.",
#             "Note that this the available values consist of old and new ones.",
#             "The new ones are all from credit.niso.org.",
#             "Both are supported in their UI, but we should only support the new ones.",
#         ],
#         kbSourceName="contributor-role",
#         kbSourceType="work:contributor -> sequence of -> contributor-attributes -> work:contributor-attributes -> sequence of -> contributor-role -> common:contributor-role",
#         kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L191",
#         kbUpstreamType="xs:string",
#         kbUpstreamTypeRef="",
#     )


class WorkType(str, Enum):
    book = "book"
    book_chapter = "book-chapter"
    book_review = "book-review"
    dictionary_entry = "dictionary-entry"
    dissertation = "dissertation"
    dissertation_thesis = "dissertation-thesis"
    encyclopedia_entry = "encyclopedia-entry"
    edited_book = "edited-book"
    journal_article = "journal-article"
    journal_issue = "journal-issue"
    magazine_article = "magazine-article"
    manual = "manual"
    online_resource = "online-resource"
    newsletter_article = "newsletter-article"
    newspaper_article = "newspaper-article"
    preprint = "preprint"
    report = "report"
    review = "review"
    research_tool = "research-tool"
    supervised_student_publication = "supervised-student-publication"
    test = "test"
    translation = "translation"
    website = "website"
    working_paper = "working-paper"
    conference_abstract = "conference-abstract"
    conference_paper = "conference-paper"
    conference_poster = "conference-poster"
    disclosure = "disclosure"
    license = "license"
    patent = "patent"
    registered_copyright = "registered-copyright"
    trademark = "trademark"
    annotation = "annotation"
    artistic_performance = "artistic-performance"
    data_management_plan = "data-management-plan"
    data_set = "data-set"
    invention = "invention"
    lecture_speech = "lecture-speech"
    physical_object = "physical-object"
    research_technique = "research-technique"
    software = "software"
    spin_off_company = "spin-off-company"
    standards_and_policy = "standards-and-policy"
    technical_standard = "technical-standard"
    other = "other"


class WorkBase(ServiceBaseModel):
    """
    Represents the core of a work record, both one persisted to ORCID
    as well as one which only exists in memory, full work record and
    summary.
    """

    title: str = Field(
        title="Title",
        description="The main name or title of the work.",
        max_length=1000,
        # custom
        # kbComment="",
        # kbSourceName="work:work-title -> common:title",
        # kbSourceType="common:string-1000",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L830",
        # kbUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#string",
    )
    date: str = Field(
        title="Date",
        description="",
        # custom
        # kbComment="should probably rename to publication date; too ambiguous now, if simpler.",
        # kbNotes=[
        #     "Note that it is 'fuzzy' because it can be year, year/month, year/month/day",
        #     "Thus cannot be converted to a date, except in the year/month/day form ",
        # ],
        # kbSourceName="work -> publication-date -> fuzzy-date, with subfields for date parts",
        # kbSourceType="common:fuzzy-date",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L623",
        # kbUpstreamTypeRef="",
    )
    workType: WorkType = Field(
        title="Work Type",
        description="The type of object that the work is, from a list of available types",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "unfortunately although the linked docs note that there is an api resource providing",
        #     "the list of types, that url redirects to a documentation page, which includes",
        #     "that information splayed out into a table.",
        # ],
        # kbSourceName="work:work-type",
        # kbSourceType="work:work-type",
        # kbSourceTypeRef="https://info.orcid.org/documentation/integration-and-api-faq/#easy-faq-2682",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    url: str = Field(
        title="URL",
        description="",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "from common.xsd: Represents a URL in the XML anyURI format",
        #     "weird, it looks like there are to entries for url in common.xsd.",
        #     "the upstream type is very broad, can include relative URLs, ",
        #     "IRIs (International RIs), etc.",
        # ],
        # kbSourceName="work:url -> common:url ",
        # kbSourceType="common:url",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L353",
        # kbUpstreamType="xs:anyURI",
        # kbUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#anyURI",
    )
    doi: str = Field(
        title="DOI",
        description="The Digitial Object Identifier (DOI) assigned to the Narrative",
        # custom
        # kbComment="This is stored, ultimately, with the externalIds, but separated for simplification.",
        # kbSourceName="",
        # kbSourceType="",
        # kbSourceTypeRef="",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    externalIds: List[ExternalId] = Field(
        title="External Ids",
        description="",
        # custom
        # kbComment="",
        # kbSourceName="work:external-ids -> common:external-ids",
        # kbSourceType="common:external-ids",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L1045",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    # TODO: is really optional? check out the schema


class FullWork(WorkBase):
    journal: str = Field(
        title="Journal",
        description=(
            "The title of the publication or group under which the work was published."
        ),
        max_length=1000,
        # custom
        # kbComment="This is an ORCID 'non-empty-string' with a cap of 1000 characters applied",
        # kbSourceName="",
        # kbSourceType="work:journal-title -> common:string-1000 -> common:non-empty-string",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L753",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    shortDescription: str = Field(
        title="Short Description",
        description="A short narrative (few sentences) describing the item.",
        max_length=5000,
        # custom
        # kbComment="This is an ORCID 'non-empty-string' with a cap of 5000 characters applied",
        # kbSourceName="",
        # kbSourceType="work:short-description -> common:short-description -> ",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L789",
        # kbUpstreamType="xs:string",
        # kbUpstreamTypeRef="",
    )
    citation: ORCIDCitation = Field(
        title="Citation",
        description="",
        # custom
        # kbComment="",
        # kbNotes=[""],
        # kbSourceName="",
        # kbSourceType="work:element-summary -> citation -> work:citation ",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L235",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    selfContributor: ORCIDContributorSelf = Field(
        title="Self Contributor",
        description="The contribution container for the owner of this work record.",
        # custom
        # kbComment="",
        # kbNotes=[
        #     "We have separated out the selfContributor in this structure to simplify",
        #     "implementation and apply different rules. E.g. the self contributor must",
        #     "have an ORCID Id (by definition!)",
        #     "Also note that this, like other fields that extend 'element-summary' gets a bunch",
        #     "of fields for free that we ignore - created, modified, source, put-code.",
        #     "ORCID itself will ignore many of these fields like put-code, and some are clearly",
        #     "only relevant for reading records from ORCID.",
        # ],
        # kbSourceName="",
        # kbSourceType="work:work -> extends common:element-summary -> contributors -> work:contributors -> contributor -> work:contributor",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L160",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )
    otherContributors: List[ORCIDContributor] = Field(
        title="Other Contributors",
        description="Container for the contributors of a Work.",
        # custom
        # kbComment="",
        # kbNotes=[""],
        # kbSourceType="work:work -> extends common:element-summary -> contributors -> work:contributors -> contributor -> work:contributor",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/record_3.0/work-3.0.xsd#L160",
        # kbUpstreamType="",
        # kbUpstreamTypeRef="",
    )


class NewWork(FullWork):
    """
    Represents a work record that is going to be added to ORCID.
    """


class PersistedWorkBase(ServiceBaseModel):
    putCode: int = Field(
        title="Put Code",
        description="Uniquely identifies a work record for a given user; required when updating or deleting a work record.",
        # custom fields
        # kbComment="Note no upstream constraints, just integer",
        # kbSourceName="put-code",
        # kbSourceType="string",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L509",
    )


class PersistedWork(PersistedWorkBase):
    createdAt: int = Field(
        title="Created At",
        description="Moment in time at which the work record was created; in epoch milliseconds.",
        # our custom fields
        # kbUnit="ms",
        # kbSourceName="created-date.value",
        # kbSourceType="xs:dateTime",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L47",
        # kbSourceUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#dateTime",
        # kbComments="Defined ultimately in the XSD datatypes documentation; Source: created-date.value; xs:dateTime; generally not required in upstream",
    )
    updatedAt: int | None = Field(
        default=None,
        title="Updated At",
        description="Moment in time at which the work record was updated; in epoch milliseconds.",
        # our custom fields
        # kbUnit="ms",
        # kbSourceName="last-modified-date.value",
        # kbSourceType="xs:dateTime",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L47",
        # kbSourceUpstreamTypeRef="https://www.w3.org/TR/xmlschema11-2/#dateTime",
        # kbComments="Defined ultimately in the XSD datatypes documentation; Source: created-date.value; xs:dateTime; generally not required in upstream",
    )

    source: str | None = Field(
        default=None,
        title="Source",
        description="Internal (generated by ORCID) field representing which entity created the work record. KBase has it's own code for CI (and in the future, prod).",
        # custom
        # kbComments="Since we now only use work activity records created by KBase, we can probably drop this field.",
        # kbSourceName="work -> source -> source-name -> value",
        # kbSourceTypeRef="https://github.com/ORCID/orcid-model/blob/e7a9c0c0060f843b2534e6100b30cab713c8aef5/src/main/resources/common_3.0/common-3.0.xsd#L107",
    )

    # journal: Optional[str] = Field(default=None)
    # shortDescription: Optional[str] = Field(default=None)
    # citation: Optional[ORCIDCitation] = Field(default=None)


class Work(FullWork, PersistedWork):
    pass


class WorkUpdate(FullWork, PersistedWorkBase):
    """
    Represents a work record which has been fetched from ORCID, modified,
    and can be sent back to update the ORCID work record
    """


# TODO: unify these work types; tricky part is that we require fields for creating
# our own work records which are optional for those created at ORCID.


class WorkSummary(WorkBase, PersistedWork):
    journal: Optional[str] = Field(default=None)

    # Note that these fields have equivalents for NewWork and WorkUpdate
    # for which they are required, since those types are for our usage of
    # works. WorkSummary and Work cover all ORCID work records, so loosen
    # these type definitions to be optional.
    # Unfortunately pydantic does not seem to allow overriding types.
    # Okay, solved (hopefully) by only working with KBase generated records,
    # which will be stricter; i.e. will always ensure that these fields
    # are populated.
    # journal: Optional[str] = Field(default=None)
    # shortDescription: Optional[str] = Field(default=None)
    # citation: Optional[ORCIDCitation] = Field(default=None)


# class ORCIDWork(ORCIDWorkSummary):
#     selfContributor: ORCIDContributorSelf = Field(...)
#     otherContributors: Optional[List[ORCIDContributor]] = Field(default=None)


# For some reason, a "work" can be composed of more than one
# work record, one of which is the "preferred". I don't yet
# know what makes a work record "preferred".
# There is a set of external ids for the group, which appears
# to be identical for each of the work records.
# We do need to model it correctly, but not quite sure
# how to interpret it...
class ORCIDWorkGroup(ServiceBaseModel):
    updatedAt: int = Field(...)
    externalIds: List[ExternalId] = Field(...)
    works: List[WorkSummary] = Field(...)


class ORCIDAffiliation(ServiceBaseModel):
    name: str = Field(...)
    role: str = Field(...)
    startYear: str = Field(...)
    endYear: Union[str, None] = Field(default=None)


F = TypeVar("F", bound=ServiceBaseModel)


class ORCIDFieldGroup(ServiceBaseModel, Generic[F]):
    private: bool = Field(...)
    fields: Optional[F] = Field(default=None)


class ORCIDNameFields(ServiceBaseModel):
    firstName: str = Field(...)
    # These fields are null if the fields are empty in the ORCID profile ui.
    lastName: Optional[str] = Field(default=None)
    creditName: Optional[str] = Field(default=None)


class ORCIDBiographyFields(ServiceBaseModel):
    bio: Optional[str] = Field(default=None)


class ORCIDEmailFields(ServiceBaseModel):
    emailAddresses: List[str] = Field(...)


# TODO: well, I think all of the fields need to be optional?
#       Need to experiment with orcid profiles to see the impact of making
#       fields private.
class ORCIDProfile(ServiceBaseModel):
    orcidId: Optional[str] = Field(default=None)
    nameGroup: ORCIDFieldGroup[ORCIDNameFields] = Field(...)
    biographyGroup: ORCIDFieldGroup[ORCIDBiographyFields] = Field(...)
    emailGroup: ORCIDFieldGroup[ORCIDEmailFields] = Field(...)
    employment: List[ORCIDAffiliation] = Field(...)


class JSONDecodeErrorData(ServiceBaseModel):
    status_code: int = Field(
        serialization_alias="status-code", validation_alias="status-code"
    )
    error: str = Field(...)


class UnknownError(ServiceBaseModel):
    exception: str = Field(...)
