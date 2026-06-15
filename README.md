# Point Once Core

Rules-based NLU chat service for Agencia TA / Point Once. FastAPI + SQLite + WhatsApp Cloud API.

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
cp .env.example .env   # edit with Meta credentials
uvicorn main:app --host 127.0.0.1 --port 3040 --workers 1
```

## Admin / config page

Panel de pruebas en el propio servicio (sin React):

```
http://127.0.0.1:3040/admin
```

Incluye:
- Estado de salud (`/health`)
- Estado de conexión WhatsApp (variables requeridas vs faltantes)
- Configuración de entorno (solo lectura, tokens enmascarados)
- **Caso 1 — Chat API:** botones que llaman `POST /chat/message`
- **Caso 2 — Webhook Mock:** botones que llaman `POST /webhook/whatsapp` (payload simple o formato Meta sin `object`)

## WhatsApp Cloud API

### Webhook URL (Meta Business Manager)

```
https://sistemataup.online/api/core/webhook/whatsapp
```

Nginx proxy: `/api/core/` → `http://127.0.0.1:3040/` (ver `deploy/nginx-landings.sistemataup.online.conf`).

### Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `WHATSAPP_TOKEN` | Sí | Access token permanente o temporal |
| `WHATSAPP_PHONE_NUMBER_ID` | Sí | ID del número en Meta (API Setup) |
| `WEBHOOK_VERIFY_TOKEN` | Sí | String personalizado para verificación GET |
| `WHATSAPP_APP_SECRET` | Recomendada | App Secret para validar `X-Hub-Signature-256` |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Opcional | WABA ID (referencia) |
| `WHATSAPP_PHONE` | Opcional | Número visible (+54 264 628-1854) |

Copiá `.env.example` a `.env` y completá los valores desde [Meta Business Manager](https://business.facebook.com/) → WhatsApp → API Setup.

### Configuración manual en Meta

1. **App Dashboard** → WhatsApp → Configuration → Webhook
2. **Callback URL:** `https://sistemataup.online/api/core/webhook/whatsapp`
3. **Verify token:** mismo valor que `WEBHOOK_VERIFY_TOKEN` en `.env`
4. Click **Verify and Save**
5. Suscríbete al campo **`messages`**
6. Generá un **access token** con permiso `whatsapp_business_messaging`
7. Copiá **Phone number ID** y token a `.env`
8. Reiniciá PM2: `pm2 restart core`

### Endpoints webhook

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/webhook/whatsapp` | Verificación Meta (`hub.mode`, `hub.verify_token`, `hub.challenge`) |
| POST | `/webhook/whatsapp` | Recibe mensajes Meta; responde vía Graph API |

Payload mock para pruebas locales (devuelve JSON de chat, no envía a Meta):

```bash
curl -s -X POST http://127.0.0.1:3040/webhook/whatsapp \
  -H 'Content-Type: application/json' \
  -d '{"phone":"5492612345678","text":"tienen stock?"}'
```

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

## Nginx (sistemataup.online)

Aplicar config con el script del monorepo Landing:

```bash
bash /home/dev_taup/proyectos/Landing/scripts/apply-nginx-landings.sh
```

Tras actualizar, el webhook queda expuesto en HTTPS vía `/api/core/`.
