# Point Once Core (Phase 1 MVP)

Rules-based NLU chat service for Agencia TA / Point Once. Lightweight FastAPI + SQLite.

**Repositorio:** https://github.com/TICIANOTAUP12/point-core

## Quick start

```bash
chmod +x scripts/start-core.sh
./scripts/start-core.sh
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 3040 --workers 1
```

## Admin / config page

Panel de pruebas en el propio servicio (sin React):

```
http://127.0.0.1:3040/admin
```

Incluye:
- Estado de salud (`/health`)
- Configuración de entorno (solo lectura)
- **Caso 1 — Chat API:** botones que llaman `POST /chat/message` (combo, stock, módulos, derivación humana)
- **Caso 2 — Webhook Mock:** botones que llaman `POST /webhook/whatsapp` (payload simple o formato Meta)

## API

### Health

```bash
curl -s http://127.0.0.1:3040/health
```

### Chat message

```bash
curl -s -X POST http://127.0.0.1:3040/chat/message \
  -H 'Content-Type: application/json' \
  -d '{"phone":"5492612345678","text":"hola quiero 2 cymax"}'
```

### WhatsApp webhook (mock)

```bash
curl -s -X POST http://127.0.0.1:3040/webhook/whatsapp \
  -H 'Content-Type: application/json' \
  -d '{"phone":"5492612345678","text":"tienen stock?"}'
```

### Debug conversation

```bash
curl -s http://127.0.0.1:3040/conversations/5492612345678
```

## Tests

```bash
source .venv/bin/activate && pytest -q
```

## PM2

Desde la raíz del repo:

```bash
pm2 start ecosystem.config.cjs
```

O desde el monorepo Landing (si aplica):

```bash
pm2 start ../ecosystem.config.cjs --only core
```

## Pending for real WhatsApp

- Meta WhatsApp Cloud API credentials (`WHATSAPP_TOKEN`, `PHONE_NUMBER_ID`)
- Webhook verification (GET challenge) and signature validation
- Outbound message send via Graph API
- Template messages for 24h window compliance
