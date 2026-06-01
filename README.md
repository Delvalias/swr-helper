# Star Wars Rebellion Helper

Local card browser for Star Wars: Rebellion and Rise of the Empire assets cached by Tabletop Simulator.

## Run Locally

```bash
python3 -m app.extract_tts --tts-path "/Users/mihailk/Library/Tabletop Simulator"
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Open <http://127.0.0.1:8001>.

## Run With Docker

Port 8000 is already used on this machine, so the compose file publishes the app on host port 8001.

```bash
docker compose up --build
```

Open <http://127.0.0.1:8001>.

## Refresh Card Assets

If the Tabletop Simulator module changes or new images are cached, regenerate the local manifest and copied assets:

```bash
python3 -m app.extract_tts --tts-path "/Users/mihailk/Library/Tabletop Simulator"
```
