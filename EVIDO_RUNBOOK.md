# Evido Supertonic TTS Runbook

Dieses Runbook beschreibt den eigenstaendigen Supertonic-3-TTS-Container fuer
Evido. Der Dienst laeuft separat vom Evido-Haupt-Compose und wird intern ueber
das Docker-Netz `evido-live-translate` erreicht.

## Zielbild

- Repository: `https://github.com/Don-K-King/supertonic`
- Evido-Service: `supertonic-tts`
- Docker-Image: `evido-supertonic-tts:1.3.1`
- Supertonic Runtime: `supertonic[serve]==1.3.1`
- Modell: `supertonic-3`
- Internes Ziel fuer Evido: `http://supertonic-tts:7788/v1/tts`
- Keine Host-Port-Freigabe im Standardbetrieb

Supertonic 3 deckt 31 Sprachen ab:

`ar`, `bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `hi`,
`hr`, `hu`, `id`, `it`, `ja`, `ko`, `lt`, `lv`, `nl`, `pl`, `pt`, `ro`,
`ru`, `sk`, `sl`, `sv`, `tr`, `uk`, `vi`.

Zusaetzlich akzeptiert Supertonic `na` als language-agnostic Fallback fuer
unbekannte oder nicht unterstuetzte Texte. `na` ist kein eigener Zielsprachcode.
Die Liste entspricht der Modelcard `Supertone/supertonic-3` und dem Fork
`Don-K-King/supertonic`.

Quellen:

- GitHub: `https://github.com/Don-K-King/supertonic`
- Hugging Face Modelcard: `https://huggingface.co/Supertone/supertonic-3`

## Netzwerkvertrag

Das externe Docker-Netz muss existieren:

```bash
docker network inspect evido-live-translate >/dev/null 2>&1 || \
  docker network create evido-live-translate
```

Der Container registriert im Netz den Alias `supertonic-tts`. Evido-Mappings
muessen deshalb als Endpoint verwenden:

```text
http://supertonic-tts:7788/v1/tts
```

Nur ein aktiver Supertonic-Container sollte diesen Alias gleichzeitig nutzen.
Wenn parallel noch ein alter Evido-Monorepo-Supertonic-Container laeuft, kann
Docker DNS beide Ziele fuer denselben Alias liefern.

## Installation

Konfiguration pruefen:

```bash
docker compose -f docker-compose.evido.yml config
```

Container bauen und starten:

```bash
docker compose -f docker-compose.evido.yml up --build -d
```

Beim ersten Start laedt Supertonic das Modell in `./models`. Wenn Docker-Bridge
Egress nicht verfuegbar ist, kann der Cache einmalig ueber Host-Networking
befuellt werden:

```bash
docker build --network host \
  -f docker/evido/Dockerfile \
  -t evido-supertonic-tts:1.3.1 .

docker run --rm --network host \
  -e HF_HOME=/models/huggingface \
  -e SUPERTONIC_CACHE_DIR=/models/supertonic3 \
  -e XDG_CACHE_HOME=/models/.cache \
  -v "$PWD/models:/models" \
  evido-supertonic-tts:1.3.1 \
  supertonic download

docker compose -f docker-compose.evido.yml up -d
```

## Verifikation

Container-Status:

```bash
docker compose -f docker-compose.evido.yml ps
```

Health:

```bash
docker run --rm --network evido-live-translate curlimages/curl:8.7.1 \
  -fsS http://supertonic-tts:7788/v1/health
```

Stimmen:

```bash
docker run --rm --network evido-live-translate curlimages/curl:8.7.1 \
  -fsS http://supertonic-tts:7788/v1/styles
```

Synthese:

```bash
docker run --rm --network evido-live-translate curlimages/curl:8.7.1 \
  -fsS -X POST http://supertonic-tts:7788/v1/tts \
  -H "Content-Type: application/json" \
  --data '{"text":"Hallo Test.","voice":"M1","lang":"de","response_format":"wav"}' \
  --output /tmp/supertonic-test.wav
```

Backend-DNS aus Evido:

```bash
docker exec evido-test-backend-1 python -c 'import urllib.request; print(urllib.request.urlopen("http://supertonic-tts:7788/v1/health", timeout=10).read().decode())'
```

## Evido TTS-Mapping

Provider-Key:

```text
supertonic
```

Pflichtfelder:

- `supertonic_parameters.voice`: eingebaute Stimme `M1` bis `M5`, `F1` bis
  `F5`, oder importierter Style.
- `supertonic_parameters.lang`: Supertonic-Basissprachcode oder `na`.

Optionale Felder:

- `response_format`: `wav`, `flac`, `ogg`
- `speed`: `0.7` bis `2.0`
- `steps`: `1` bis `100`
- `max_chunk_length`: `1` bis `10000`
- `silence_duration`: `0` bis `10`

Evido leitet den regionalen Sprachcode nicht automatisch ab. Regionale Codes
wie `de-DE`, `en-US`, `fr-FR`, `bg-BG` oder `es-ES` muessen explizit auf
Supertonic-Basiscodes wie `de`, `en`, `fr`, `bg` oder `es` gemappt werden.

Aktuell bewaehrtes Beispiel:

```json
{
  "language_code": "de-DE",
  "provider_key": "supertonic",
  "priority": 1,
  "enabled": true,
  "config": {
    "endpoint": "http://supertonic-tts:7788/v1/tts",
    "supertonic_parameters": {
      "voice": "M1",
      "lang": "de",
      "response_format": "wav"
    }
  }
}
```

Weitere Beispiele liegen in `examples/evido-tts-mappings.json`.

## Custom Voices

Voice-Builder-JSON-Dateien werden lokal unter `voices/custom/*.json` abgelegt.
Diese Dateien werden nicht versioniert.

Import gegen den internen Dienst:

```bash
./scripts/import-supertonic-voices.sh
```

Wichtige Variablen:

```bash
SUPERTONIC_VOICE_DIR=./voices/custom
SUPERTONIC_BASE_URL=http://supertonic-tts:7788
SUPERTONIC_IMPORT_OVERWRITE=true
SUPERTONIC_IMPORT_USE_DOCKER=1
SUPERTONIC_DOCKER_NETWORK=evido-live-translate
```

## Troubleshooting

- `Temporary failure in name resolution`: pruefen, ob Evido-Backend und
  Supertonic im Netz `evido-live-translate` haengen und ob der Alias
  `supertonic-tts` vorhanden ist.
- Timeout zu Hugging Face oder externen Hosts: Docker-Bridge-Egress, nftables
  Forward-Regeln und NAT/MASQUERADE fuer Docker-Subnetze pruefen.
- Modellcache leer oder Download haengt: Host-Network-Predownload aus der
  Installationssektion verwenden.
- `unsupported_lang`: `supertonic_parameters.lang` muss einer der 31 Codes
  oder `na` sein.
- Custom Voice nicht sichtbar: Import-Response pruefen und danach
  `GET /v1/styles` erneut ausfuehren.
- Falscher Zielcontainer: sicherstellen, dass nicht zwei Container gleichzeitig
  den Alias `supertonic-tts` im selben Docker-Netz verwenden.
