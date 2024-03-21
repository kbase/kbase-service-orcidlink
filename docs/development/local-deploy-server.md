#

build image


create sandbox or prod env:

```shell
source ./Taskfile orcid-sandbox-env 'ORCID CLIENT ID' 'ORCID CLIENT SECRET'
```

start server

KBASE_ENDPOINT=https://ci.kbase.us/services/  ./Taskfile server