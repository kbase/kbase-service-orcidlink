# Testing

When in the devcontainer:

```shell
export PYTHONPATH="${PWD}/src"
SERVICE_DIRECTORY=/workspace ./tools/scripts/run-tests.sh
```

From host:

```shell
./Taskfile test
```
