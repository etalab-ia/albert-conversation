# Getting started

Before using the *OpenWebUI* frontend, you need to start the backend. Follow [`backend/README.md`](backend/README.md) to get started.

Install frontend dependencies:

```sh
$ mise install
$ npm install # 1.9G installed
$ pnpm run dev:frontend
```

Next, open your browser on <http://localhost:5173/>.

You can connect as administrator at the following URL: <http://localhost:5173/logadmin>.

Default admin user is:

- email: `admin@example.com`
- password: `password`

## Useful subdirectories

You can use the [`/deployment-playground/`](./deployment-playground/) directory to test the [`ghcr.io/etalab-ia/albert-conversation/app`](https://github.com/etalab-ia/albert-conversation/pkgs/container/albert-conversation%2Fapp) Docker image locally, in an environment that resembles the production environment.
