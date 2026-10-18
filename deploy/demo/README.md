# Client demo (test.davoskarting.ir)

A demo, not production: sign-in codes are shown on the page, "payment" goes through a pretend bank page (`demo_bank.py`,
no money), the server is a 1 GB machine. Nothing here is meant for real customers.

## What a push does

`.github/workflows/deploy-demo.yml` runs on every push to `feature/semantic-cache` (or by hand under Actions → deploy-demo →
Run workflow). It builds the API and web images on GitHub's runner, copies the code and the images to the server over SSH,
restarts the services with `docker-compose up -d --no-build` (the `migrate` job runs first) and checks the public pages.

## One-time setup

1. The server already trusts the deploy key's public half (`davos-github-actions` in root's `authorized_keys`).
2. GitHub → the repository → Settings → Secrets and variables → Actions → New repository secret:
   name `DEPLOY_SSH_KEY`, value = the whole content of the private key file `~/.ssh/davos_actions` (including the
   `-----BEGIN` and `-----END` lines). Never paste it anywhere else.
3. The server's `.env` is made once with `python3 deploy/demo/make_env.py test.davoskarting.ir` and is never touched by a
   deploy (the workflow excludes it). To change a setting, edit it on the server and run the workflow again.

## Files

- `make_env.py`: generates `.env` with fresh random secrets for this demo.
- `docker-compose.demo.yml`: layered over `docker-compose.yml` (never together with `docker-compose.override.yml`).
- `nginx-test.davoskarting.ir.conf`: the host nginx's vhost (HTTPS with a Cloudflare origin certificate).
- `demo_bank.py` + `fake_mellat.py`: the pretend bank. `frontend.Dockerfile`: only needed when the web image is built on
  the server itself (an Alpine mirror), which the workflow no longer does.
