# Errors

All errors returned from the service comply with a simple format:

- code - an integer between 1000 and 1999, defined in `lib/errors.py`
- title - a suggested title for the error, meant for display to users to announce it, e.g. in an error dialog format; the title is invariant wrt the code
- message - the error message is the primary communication of the problem encountered; it is generated at the site at which the problem is detected; it should be fairly specific; it should be no longer than a sentence.
- data - an optional object further describing the error; the data object should only contain information useful for presenting to a user, or for an interface to utilize in some other way. 

FastAPI provides an "exception catcher" mechanism by which any exception raised and escaping an endpoint can be caught and the specific response crafted. The orcidlink service relies up on this mechanism heavily. Most problems are signaled by raising an exception defined in `lib/exceptions.py`, and mirror the errors defined in `lib/errors.py`. 

## "Interactive" errors

The oauth flow relies upon the browser actually visiting the orcidlink service. This "visit" is temporary, and leads immediately to a redirect to the orcidlink ui hosted in kbase-ui. The orcidlink service does not have any user interface. Therefore, if something goes wrong, orcidlink forms a special redirect to an error page in the orcidlink ui, placing error information in the redirect url.

The orcidlink ui error page makes a call back to the orcidlink service to fetch information about the specific error, given the error code.

## Expected vs Unexpected Errors

Some errors are expected to occur from time to time, some are edge cases but need to be handled explicitly, and others are either extreme edge cases or only possible due to internal bugs.

Examples of expected errors include:
- expired kbase token, resulting in an `authorization_required` error
- not found (`not_found`)- e.g. backing up into the `#orcidlink/revoke` page after the link has been removed will result in a "404" response when the page attempts to fetch the link information.

Edge cases include:
- not authorized at ORCID (`authorization_required`) - this should probably be a bespoke error
- orcid id already linked (`linking_session_already_linked`)
- kbase account already linked (`already_linked`)

Unexpected errors include:
- json_decode_error, content_type_error - can occur if a dependent service returns a true 500 response with text
- request_validation_error - can occur when the api is mis-used (i.e. parameters are provided by are incorrect)

## Scoping of Errors

The basic philosopy of error scope is that if an error is expected or an edge case, we should have an error as specific as we need it, with a data property providing additional information, if necessary.

Sometimes, given the context, a broadly scoped error like `not_found` is sufficient.

Unexpected errors don't need to be narrow in scope (take `upstream_error`), but they should have a message which describes the location, and may need to have an exception trace to help debug it.

General exceptions, like `ValueError`, or those raised by libraries are pretty much left to be caught by the catch-all error handler in `main.py`. These errors include the stack trace.

## Status

Some errors which could have a data attribute do not. This is simply because I've not had the time to think about it and implement it. 

Error naming should be refactored.

There are surely cases in which a more bespoke error is called for.