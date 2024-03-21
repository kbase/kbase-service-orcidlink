import json
import sys

from fastapi.openapi.utils import get_openapi

from orcidlink.main import app


def main():
    dest = sys.argv[1]
    with open(f"{dest}/docs/api/openapi.json", "w", encoding="utf-8") as out:
        json.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
                tags=app.openapi_tags,
                terms_of_service=app.terms_of_service,
                contact=app.contact,
                license_info=app.license_info,
                # openapi_prefix=app.openapi_prefix,
            ),
            out,
            indent=4,
        )


main()
