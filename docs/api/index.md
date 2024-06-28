<a name="header_orcid-link-service"></a>
# ORCID Link Service
<table><tr><td>version: 0.1.0</td></tr></table>


The *ORCID Link Service* provides an API to enable the linking of a KBase
 user account to an ORCID account. This "link" consists of a [Link
 Record](#user-content-header_type_linkrecord) which contains a KBase username, ORCID
 id, ORCID access token, and a few other fields. This link record allows KBase to create
 tools and services which utilize the ORCID api to view or modify certain aspects of a
 users ORCID profile.

Once connected, *ORCID Link* enables certain integrations, including:

- syncing your KBase profile from your ORCID profile
- creating and managing KBase public Narratives within your ORCID profile
<a name="header_terms-of-service"></a>
## Terms of Service
<a href="https://www.kbase.us/about/terms-and-conditions-v2/">https://www.kbase.us/about/terms-and-conditions-v2/</a>
<a name="header_contact"></a>
## Contact
KBase, Lawrence Berkeley National Laboratory, DOE  
<a href="https://www.kbase.us/">https://www.kbase.us/</a>  
engage@kbase.us
<a name="header_license"></a>
## License
The MIT License
<a href="https://github.com/kbase/kb_sdk/blob/develop/LICENSE.md">https://github.com/kbase/kb_sdk/blob/develop/LICENSE.md</a>
## Usage

This document is primarily generated from the `openapi` interface generated 
by <a href="https://fastapi.tiangolo.com">FastAPI</a>.

The [Endpoints](#user-content-header_endpoints) section documents all REST endpoints, including the 
expected responses, input parameters and output JSON and type definitions.

The [Types](#user-content-header_types) section defines all of the Pydantic models used in the codebase, 
most of which are in service of the input and output types mentioned above.

### Issues

- Due to limitations of GitHub's markdown support, tables have two empty rows at the start of the header. This is due to the fact that GitHub does not allow any table formatting instructions, so we need to use the first two rows to establish the table and column widths. 

## Table of Contents    

- [Endpoints](#user-content-header_endpoints)
    - [misc](#user-content-header_misc)
    - [link](#user-content-header_link)
    - [linking-sessions](#user-content-header_linking-sessions)
    - [orcid](#user-content-header_orcid)
    - [works](#user-content-header_works)
- [Types](#user-content-header_types)
- [Glossary](#user-content-header_glossary)


<a name="header_endpoints"></a>
## Endpoints
<a name="header_jsonrpc"></a>
### jsonrpc
JSON-RPC 2.0 method
<a name="header_post-/api/v1"></a>
#### POST /api/v1
n/a


<a name="header_input"></a>
#### Input
*none*


<a name="header_output"></a>
#### Output
<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><tr><th>Status Code</th><th>Description</th><th>Type</th></tr></thead><tbody><tr><td>200</td><td>Successful Response</td><td><a href="#user-content-header_type__response">_Response</a></td></tr><tr><td>210</td><td>[1010] Authorization Required</td><td><a href="#user-content-header_type__errorresponse_authorizationrequirederror_">_ErrorResponse_AuthorizationRequiredError_</a></td></tr><tr><td>211</td><td>[1011] Not Authorized</td><td><a href="#user-content-header_type__errorresponse_notauthorizederror_">_ErrorResponse_NotAuthorizedError_</a></td></tr><tr><td>212</td><td>[1020] Not Found</td><td><a href="#user-content-header_type__errorresponse_notfounderror_">_ErrorResponse_NotFoundError_</a></td></tr><tr><td>213</td><td>[-32602] Invalid params

Invalid method parameter(s)</td><td><a href="#user-content-header_type__errorresponse_invalidparams_">_ErrorResponse_InvalidParams_</a></td></tr><tr><td>214</td><td>[-32601] Method not found

The method does not exist / is not available</td><td><a href="#user-content-header_type__errorresponse_methodnotfound_">_ErrorResponse_MethodNotFound_</a></td></tr><tr><td>215</td><td>[-32700] Parse error

Invalid JSON was received by the server</td><td><a href="#user-content-header_type__errorresponse_parseerror_">_ErrorResponse_ParseError_</a></td></tr><tr><td>216</td><td>[-32600] Invalid Request

The JSON sent is not a valid Request object</td><td><a href="#user-content-header_type__errorresponse_invalidrequest_">_ErrorResponse_InvalidRequest_</a></td></tr><tr><td>217</td><td>[-32603] Internal error

Internal JSON-RPC error</td><td><a href="#user-content-header_type__errorresponse_internalerror_">_ErrorResponse_InternalError_</a></td></tr><tr><td>default</td><td>Default Response</td><td><i>none</i></td></tr></tbody></table>


---


<a name="header_misc"></a>
### misc
Miscellaneous operations
<a name="header_get-/docs"></a>
#### GET /docs
Get API Documentation

Provides a web interface to the auto-generated API docs.


<a name="header_input"></a>
#### Input
*none*


<a name="header_output"></a>
#### Output
<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><tr><th>Status Code</th><th>Description</th><th>Type</th></tr></thead><tbody><tr><td>200</td><td>Successfully returned the api docs</td><td>text/html</td></tr><tr><td>404</td><td>Not Found</td><td><i>none</i></td></tr></tbody></table>


---


<a name="header_link"></a>
### link
Access to and control over stored ORCID Links


<a name="header_linking-sessions"></a>
### linking-sessions
OAuth integration and internal support for creating ORCID Links.

The common path element is `/linking-sessions`.

Some of the endpoints are "browser interactive", meaning that the links are followed
directly by the browser, rather than being used within Javascript code.
<a name="header_get-/linking-sessions/{session_id}/oauth/start"></a>
#### GET /linking-sessions/{session_id}/oauth/start
Start Linking Session

This endpoint is designed to be used directly by the browser. It is the "start"
of the ORCID OAuth flow. If the provided session id is found and the associated
session record is still in the initial state, it will initiate the OAuth flow
by redirecting the browser to an endpoint at ORCID.

Starts a "linking session", an interactive OAuth flow the end result of which is an
access_token stored at KBase for future use by the user.


<a name="header_input"></a>
#### Input
<table><thead><tr><th colspan="4"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><th><img width="150px"></th><tr><th>Name</th><th>Description</th><th>Type</th><th>In</th></tr></thead><tbody><tr><td>session_id</td><td>The linking session id</td><td>string</td><td>path</td></tr><tr><td>return_link</td><td>A url to redirect to after the entire linking is complete; not to be confused with the ORCID OAuth flow's redirect_url</td><td>n/a</td><td>query</td></tr><tr><td>skip_prompt</td><td>Whether to prompt for confirmation of linking</td><td>boolean</td><td>query</td></tr><tr><td>ui_options</td><td>Opaque string of ui options</td><td>string</td><td>query</td></tr><tr><td>kbase_session</td><td>KBase auth token taken from a cookie named 'kbase_session'</td><td>n/a</td><td>cookie</td></tr><tr><td>kbase_session_backup</td><td>KBase auth token taken from a cookie named 'kbase_session_backup. Required in the KBase production environment since the prod ui and services operate on different hosts; the primary cookie, kbase_session, is host-based so cannot be read by a prod service.</td><td>n/a</td><td>cookie</td></tr></tbody></table>


<a name="header_output"></a>
#### Output
<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><tr><th>Status Code</th><th>Description</th><th>Type</th></tr></thead><tbody><tr><td>302</td><td>Redirect to ORCID if a valid linking session, back to KBase in the case of an error</td><td><i>none</i></td></tr><tr><td>401</td><td>KBase auth token absent or invalid</td><td><i>none</i></td></tr><tr><td>422</td><td>Input or output data does not comply with the API schema</td><td><i>none</i></td></tr></tbody></table>


---
<a name="header_get-/linking-sessions/oauth/continue"></a>
#### GET /linking-sessions/oauth/continue
Continue Linking Session

This endpoint implements the handoff from from the ORCID authorization step in
the ORCID OAuth flow. That is, it
serves as the redirection target after the user has successfully completed
their interaction with ORCID, at which they may have logged in and provided
their consent to issuing the linking token to KBase.

Note that this is an interstitional endpoint, which does not have its own
user interface. Rather, it redirects to kbase-ui when finished. If an error is
encountered, it redirects to an error viewing endpoint in kbase-ui.


<a name="header_input"></a>
#### Input
<table><thead><tr><th colspan="4"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><th><img width="150px"></th><tr><th>Name</th><th>Description</th><th>Type</th><th>In</th></tr></thead><tbody><tr><td>code</td><td>For a success case, contains an OAuth exchange code parameter</td><td>n/a</td><td>query</td></tr><tr><td>state</td><td>For a success case, contains an OAuth state parameter</td><td>n/a</td><td>query</td></tr><tr><td>error</td><td>For an error case, contains an error code parameter</td><td>n/a</td><td>query</td></tr><tr><td>kbase_session</td><td>KBase auth token taken from a cookie named 'kbase_session'</td><td>n/a</td><td>cookie</td></tr><tr><td>kbase_session_backup</td><td>KBase auth token taken from a cookie named 'kbase_session_backup. Required in the KBase production environment since the prod ui and services operate on different hosts; the primary cookie, kbase_session, is host-based so cannot be read by a prod service.</td><td>n/a</td><td>cookie</td></tr></tbody></table>


<a name="header_output"></a>
#### Output
<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="150px"></th><th><img width="1000px"></th><th><img width="150px"></th><tr><th>Status Code</th><th>Description</th><th>Type</th></tr></thead><tbody><tr><td>302</td><td>Redirect to the continuation page; or error page</td><td><i>none</i></td></tr><tr><td>401</td><td>Linking requires authorization; same meaning as standard auth 401, but caught and issued in a different manner</td><td><i>none</i></td></tr><tr><td>422</td><td>Input or output data does not comply with the API schema</td><td><i>none</i></td></tr></tbody></table>


---


<a name="header_orcid"></a>
### orcid
Direct access to ORCID via ORCID Link


<a name="header_works"></a>
### works
Add, remove, update 'works' records for a user's ORCID Account


<a name="header_types"></a>
## Types
This section presents all types defined via FastAPI (Pydantic). They are ordered
alphabetically, which is fine for looking them up, but not for their relationships.

> TODO: a better presentation of related types

<a name="header_type_authorizationrequirederror"></a>
##### AuthorizationRequiredError

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type_internalerror"></a>
##### InternalError

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type_invalidparams"></a>
##### InvalidParams

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr><tr><td>data</td><td><div><i>Any Of</i></div><div><a href="#user-content-header_type__errordata__error_">_ErrorData__Error_</a></div><div>null</div></td><td></td></tr></tbody></table>



<a name="header_type_invalidrequest"></a>
##### InvalidRequest

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr><tr><td>data</td><td><div><i>Any Of</i></div><div><a href="#user-content-header_type__errordata__error_">_ErrorData__Error_</a></div><div>null</div></td><td></td></tr></tbody></table>



<a name="header_type_methodnotfound"></a>
##### MethodNotFound

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type_notauthorizederror"></a>
##### NotAuthorizedError

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type_notfounderror"></a>
##### NotFoundError

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type_parseerror"></a>
##### ParseError

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>code</td><td>integer</td><td></td></tr><tr><td>message</td><td>string</td><td></td></tr></tbody></table>



<a name="header_type__error"></a>
##### _Error

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>loc</td><td>array</td><td>✓</td></tr><tr><td>msg</td><td>string</td><td>✓</td></tr><tr><td>type</td><td>string</td><td>✓</td></tr><tr><td>ctx</td><td><div><i>Any Of</i></div><div>object</div><div>null</div></td><td></td></tr></tbody></table>



<a name="header_type__errordata__error_"></a>
##### _ErrorData__Error_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>errors</td><td><div><i>Any Of</i></div><div>array</div><div>null</div></td><td></td></tr></tbody></table>



<a name="header_type__errorresponse_authorizationrequirederror_"></a>
##### _ErrorResponse_AuthorizationRequiredError_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_authorizationrequirederror">AuthorizationRequiredError</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_internalerror_"></a>
##### _ErrorResponse_InternalError_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_internalerror">InternalError</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_invalidparams_"></a>
##### _ErrorResponse_InvalidParams_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_invalidparams">InvalidParams</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_invalidrequest_"></a>
##### _ErrorResponse_InvalidRequest_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_invalidrequest">InvalidRequest</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_methodnotfound_"></a>
##### _ErrorResponse_MethodNotFound_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_methodnotfound">MethodNotFound</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_notauthorizederror_"></a>
##### _ErrorResponse_NotAuthorizedError_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_notauthorizederror">NotAuthorizedError</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_notfounderror_"></a>
##### _ErrorResponse_NotFoundError_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_notfounderror">NotFoundError</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__errorresponse_parseerror_"></a>
##### _ErrorResponse_ParseError_

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>error</td><td><a href="#user-content-header_type_parseerror">ParseError</a></td><td>✓</td></tr></tbody></table>



<a name="header_type__request"></a>
##### _Request

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td></td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td></td></tr><tr><td>method</td><td>string</td><td>✓</td></tr><tr><td>params</td><td>object</td><td></td></tr></tbody></table>



<a name="header_type__response"></a>
##### _Response

<table><thead><tr><th colspan="3"><img width="2000px"></th></tr><tr><th><img width="1000px"></th><th><img width="200px"></th><th><img width="75px"></th><tr><th>Name</th><th>Type</th><th>Required</th></tr></thead><tbody><tr><td>jsonrpc</td><td>string</td><td>✓</td></tr><tr><td>id</td><td><div><i>Any Of</i></div><div>string</div><div>integer</div></td><td>✓</td></tr><tr><td>result</td><td>object</td><td>✓</td></tr></tbody></table>



<a name="header_glossary"></a>
## Glossary
<dl>
<dt><a name="glossary_term_orcid"></a><a href='https://orcid.org'>ORCID</a></dt><dd>Open Researcher and Contributor ID
<dt><a name="glossary_term_public-link-record"></a>Public link record</dt><dd>The record used internally to associate a KBase User Account with an ORCID Account, with sensitive information such as tokens removed. Represented by the type <a href="#user-content-header_type_linkrecordpublic">LinkRecordPublic</a></dd>
</dl>
-fin-