# OAuth Workflow

Most parts of the API are straightforward RESTish endpoints. One makes a request - GET, POST, PUT, DELETE - and gets a response, either the expected result or an error structure.

However, the key reason for the existence of this service, the raison d'etre, is the OAuth Linking Workflow. This is a classic "3-legged" process. The legs refer to the fact that it requires 3 participating services - the target service (ORCID), the facilitating service (ORCIDLInk), and a client (ORCIDLink UI via kbase-ui).

## Linking Flow

1. User accesses the ORCIDLink UI at `#orcidlink`
2. The user clicks a button prompting then to create ad ORCID Link.
3. The ORCID Link UI presents a view with more information about what the link is, and another button to confirm; user clicks this button
4. The browser visits the ORCID Link service, which then redirects it to the ORCID OAuth endpoint
5. The user logs into ORCID
6. The user gives permission to KBase to access their account
7. The browser visits the ORCID Link service, which then redirects back to the ORCID Link UI
8. The ORCID Link UI presents the ORCID Link account that can be linked, and a button to confirm the link; user clicks the button to confirm
9. The ORCID Link UI redirects to the `#orcidlink` home page, which now shows the user information about their link, and options for it (show in profile or not, remove the link)

## Linking via User Profile Flow

1. User accesses their user profile at `#people`
2. The user clicks a button prompting then to create an ORCID Link.
3. This shows the ORCID Link UI, which presents a view with more information about what the link is, lets the user know they will return to the User Profile after linking, and a button to continue; user clicks this button
4. The browser visits the ORCID Link service, which then redirects it to the ORCID OAuth endpoint
5. The user logs into ORCID
6. The user gives permission to KBase to access their account
7. The browser visits the ORCID Link service, which then redirects back to the ORCID Link UI
8. The ORCID Link UI presents the ORCID Link account that can be linked, a message that they will return the User Profile afterwards, and a button to confirm the link; user clicks the button to confirm
9. The ORCID Link UI redirects to the User Profile UI, which now shows the ORCID Id embedded in their profile.