# Albert Conversation local deployment playground

This folder contains a local deployment playground for [`albert-conversation`](https://github.com/etalab-ia/albert-conversation/) ([Open WebUI](https://github.com/open-webui/open-webui) fork) connected to [Albert API](https://github.com/etalab-ia/albert-api/), based on `docker-compose.yml` method.

Although this is not necessary for a minimalist deployment, I chose here to configure the following options:

- connect *Albert Conversation* to a *PostgreSQL* database instead of *SQLite* ([resource about this](https://docs.openwebui.com/getting-started/env-configuration/#database-pool))
- connect *Albert Conversation* to a *Minio* instance instead of local file system storage ([resource about this](https://docs.openwebui.com/tutorials/s3-storage/))
- connect *Albert Conversation* to a *Redis* instance ([resource about this](https://docs.openwebui.com/tutorials/integrations/redis/))

## Préparation

Install [Mise](https://mise.jdx.dev/)

```sh
$ cp .secret.skel .secret
```

Then fill in the `.secret`.


## Getting started

```sh
$ mise install
```

If needed, you can force the environment variables loading with this command:

```sh
$ source .envrc
```

```sh
$ ./scripts/create-minio-bucket.sh
$ docker compose up -d --wait
$ ./scripts/create-admin-user.sh
```

Open your browser on http://localhost:8080 (admin email: `admin@example.com`, password: `password`)
