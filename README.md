# Albert Conversation a Open WebUI fork

This repository contains a soft fork of [Open WebUI](https://github.com/open-webui/open-webui).

This Albert Conversation source code is deployed on:

- https://albert.numerique.gouv.fr/
- and https://albert-dev.beta.numerique.gouv.fr/

The deployment scripts are hosted in <https://github.com/numerique-gouv/lasuite-deploiement/tree/albert-conv-conf-updates>.

It mainly includes modifications to the development environment, adding tools and scripts that correspond to my preferred working paradigm.  
I am aware that these changes reflect my preferences, which is why, having never contributed to Open WebUI, I decided it would be best to keep these patches in my fork, in a branch named `sklein-main`.

**Upstream README: [`./README-upstream.md`](./README-upstream.md)**

Here are the main changes I made:

- Moving `README.md` upstream to `README-upstream`
- Using [Mise](https://mise.jdx.dev/) to install specific versions of Python and Node in an isolated environment
- Use of automatic loading of environment variables with Mise, similar to what I could do with [Direnv](https://direnv.net/) (see note https://notes.sklein.xyz/2024-12-19_1709/)
- By default, use PostgreSQL rather than SQLite
- By default, use Redis
- By default, access LLMs via OpenRouter

## Preparing the local development environment

### Prerequisites

You must have installed:

- [Mise](https://mise.jdx.dev/installing-mise.html)
- [Docker](https://docs.docker.com/engine/install/)

I tested the instructions in this README.md only under Fedora 42, but it should work under other Linux distributions and MacOS with little adaptation.

### Getting start

```sh
$ mise install
$ source .envrc
$ docker compose -f docker-compose.sklein.yaml up -d --wait # or ./scripts/up.sh
$ pip install -r backend/requirements-minimal.txt
$ npm install --force
```

```sh
$ cp .secret.skel .secret
```

Fill `.secret` with https://openrouter.ai/ API key.

Check your API Key:

```sh
$ ./scripts/check-openroute-connection.sh
{"data":{"label":"sk-...","limit":1,"usage":0,"is_provisioning_key":false,"limit_remaining":1,"is_free_tier":false,"rate_limit":{"requests":20,"interval":"10s"}}}
```

**Start Open WebUI Python backend:**

```sh
$ cd backend
$ ./dev.sh
v0.6.15 - building the best AI user interface.

https://github.com/open-webui/open-webui

WARNI [open_webui.main] Frontend build directory not found at '/home/stephane/git/github.com/open-webui/open-webui/build'. Serving API only.
INFO:     Started server process [731000]
INFO:     Waiting for application startup.
2025-07-15 23:55:23.995 | INFO     | open_webui.utils.logger:start_logger:140 - GLOBAL_LOG_LEVEL: DEBUG - {}
2025-07-15 23:55:23.996 | INFO     | open_webui.main:lifespan:514 - Installing external dependencies of functions and tools... - {}
2025-07-15 23:55:24.021 | INFO     | open_webui.utils.plugin:install_frontmatter_requirements:241 - No requirements found in frontmatter. - {}
2025-07-15 23:55:24.022 | DEBUG    | open_webui.socket.main:periodic_usage_pool_cleanup:111 - Running periodic_usage_pool_cleanup - {}
```

Create Open WebUI admin user:

```sh
$ ./scripts/create-admin-user.sh
{"id":"85e6d0c5-3ea8-4947-821e-82b34cba6150","email":"admin@example.com","name":"admin","role":"admin", ...
```

**Start Open WEbUI SvelteKit frontend:**

```sh
$ npm run dev
```

Open your browser on <http://localhost:5173/logadmin/>.

Login with :

- Username: `admin@example.com`
- Password: `password`

## Helper scripts

```sh
$ ./scripts/get-open_webui-api-token.sh
eyJhbGciOiJIUzI1NiI...
```

```sh
$ ./scripts/enter-in-redis.sh
127.0.0.1:6379> keys *
1) "open-webui:config:OPENAI_API_KEYS"
2) "open-webui:config:ENABLE_OPENAI_API"
3) "open-webui:config:OPENAI_API_CONFIGS"
4) "open-webui:config:OPENAI_API_BASE_URLS"
5) "open-webui:config:ENABLE_SIGNUP"
```

```sh
$ ./scripts/get-models-list.sh | head
"Switchpoint Router"
"MoonshotAI: Kimi K2 (free)"
"MoonshotAI: Kimi K2"
"THUDM: GLM 4.1V 9B Thinking"
"Mistral: Devstral Medium"
"Mistral: Devstral Small 1.1"
"Venice: Uncensored (free)"
"xAI: Grok 4"
"Google: Gemma 3n 2B (free)"
"Tencent: Hunyuan A13B Instruct (free)"
```

```sh
$ ./scripts/get-pipelines-list.sh
{
  "data": [
    {
      "url": "http://localhost:32772",
      "idx": 1
    }
  ]
}
```

## Teardown

```sh
$ ./scripts/teardown.sh
```
