# OpenWebUI backend

This backend is implemented in Python.

```sh
$ mise install
$ pip install -r requirements.txt # Warning, 7.5GB of disk space used after installation
```

```sh
$ cp .secret.skel .secret
```

Configure the parameters in the `.secret` file.

```sh
$ source .envrc
```

Check that OpenAPI access is working correctly:

```sh
$ ./scripts/check-openapi-api-connection.sh
{
  "object": "list",
  "data": [
    {
      "id": "albert-small",
      "created": 1746611077,
      "object": "model",
      "owned_by": "Albert API",
      "max_context_length": 64000,
      "type": "text-generation",
      "aliases": [
        "meta-llama/Llama-3.1-8B-Instruct"
      ]
    },
...
```

Start Redis server:

```
$ docker compose up -d --wait
```

Start OpenWebUI backend:

```sh
$ ./dev.sh
INFO:     Will watch for changes in these directories: ['/home/stephane/git/github.com/stephane-klein/albert-conversation-sklein-patchs/upstream/backend']
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [170043] using WatchFiles
...
INFO:     Application startup complete.
```

Wait for "Application startup complete." log message then, if not previously done, create admin user:

```
$ ./scripts/create-admin-user.sh
Default admin user is:

- email: admin@example.com
- password: password
- name: Admin
```

Then follow the instructions in [`../README.sklein.md`](../README.sklein.md).

## Data reset

If you want to reset the data, run the following commands:

```sh
$ docker compose down -v
$ rm data/webui.db
$ docker compose up -d --wait
$ ./dev.sh
```
