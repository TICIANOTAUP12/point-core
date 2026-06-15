# Point Once Core

Rules-based NLU chat service for Agencia TA / Point Once. FastAPI + SQLite.

**Integración:** el bot arma el link `wa.me` y el consumidor cierra por WhatsApp. **No usa Cloud API por defecto.**

**Repositorio:** https://github.com/TICIANOTAUP12/point-core

## Modelo de integración (link redirect)

1. El consumidor escribe o elige una intención (precio, stock, combo, etc.).
2. Core procesa con NLU y devuelve `{ reply, whatsapp_url, needs_human }`.
3. La landing o el panel abre `whatsapp_url` → WhatsApp con mensaje prellenado.
4. **Un humano de Agencia TA cierra la conversación en WhatsApp.**

No se requieren tokens Meta ni webhook nginx para este flujo. La landing Point Once (`Agencia_TA`) usa `whatsapp.ts` client-side con el mismo patrón.

### Modo API (opcional, desactivado por defecto)

Si necesitás respuestas automáticas vía WhatsApp Cloud API, configurá `WHATSAPP_MODE=api` y las credenciales Meta. Ver sección [Cloud API opcional](#cloud-api-opcional).

## Quick start

```bash
chmod +x scripts/start-core.sh
./scripts/start-core.sh
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # WHATSAPP_MODE=link por defecto
uvicorn main:app --host 127.0.0.1 --port 3040 --workers 1
```

## Admin / config page

Panel de pruebas en el propio servicio (sin React):

```
http://127.0.0.1:3040/admin
```

Incluye:
- Estado de salud (`/health`)
- Modo de integración WhatsApp (`link` o `api`)
- Configuración de entorno (solo lectura)
- **Generar link wa.me** vía `POST /chat/message` o `POST /link/generate`
- Link generado visible con botón "Abrir en WhatsApp"

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `WHATSAPP_MODE` | `link` | `link` = wa.me redirect; `api` = Cloud API |
| `WHATSAPP_PHONE` | `+54 264 628-1854` | Número visible (solo dígitos en el link) |
| `CORE_HOST` | `127.0.0.1` | Host del servicio |
| `CORE_PORT` | `3040` | Puerto del servicio |

En modo `link` no hace falta configurar tokens Meta.

## API

### Health

```bash
curl -s http://127.0.0.1:3040/health
```

### Chat message (NLU + link)

```bash
curl -s -X POST http://127.0.0.1:3040/chat/message \
  -H 'Content-Type: application/json' \
  -d '{"phone":"5492612345678","text":"hola quiero 2 cymax"}'
```

Respuesta:

```json
{
  "reply": "¡Genial! El Puesto Cymax Completo...",
  "whatsapp_url": "https://wa.me/542646281854?text=Hola%2C%20me%20interesan%202%20Puesto%28s%29...",
  "intents": [{"type": "combo_compra", "args": {"combo_id": "cymax", "cantidad": 2}}],
  "state": "confirming",
  "needs_human": false
}
```

### Link generate (intent predefinido)

```bash
curl -s -X POST http://127.0.0.1:3040/link/generate \
  -H 'Content-Type: application/json' \
  -d '{"intent":"consulta_stock"}'
```

También acepta `{ "text": "tienen stock?" }` o `{ "phone": "5492612345678", "text": "..." }`.

### Debug conversation

```bash
curl -s http://127.0.0.1:3040/conversations/5492612345678
```

## Ejemplos de URLs por intent

| Intent / consulta | Mensaje prellenado (resumen) |
|-------------------|------------------------------|
| `consulta_stock` | "Hola, consulto disponibilidad de stock de equipos Point Once..." |
| `consulta_licencia` | "Hola, ya tengo mi equipo y quisiera consultar el precio de la licencia..." |
| `modulo_locales` | "Hola, me interesa el módulo de Locales de Point Once..." |
| `implementar` | "Hola, quiero implementar Point Once en mi comercio..." |
| Combo Cymax ×2 | "Hola, me interesan 2 Puesto(s) Cymax Completo — total estimado: $2.100.000..." |
| Derivación humana | "Hola, consulto desde la web de Point Once. Mi consulta: ... Quisiera hablar con el equipo." |

Todas las URLs siguen el formato:

```
https://wa.me/542646281854?text=<mensaje codificado>
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

## Cloud API opcional

Solo si `WHATSAPP_MODE=api`:

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `WHATSAPP_TOKEN` | Sí | Access token Meta |
| `WHATSAPP_PHONE_NUMBER_ID` | Sí | Phone number ID |
| `WEBHOOK_VERIFY_TOKEN` | Sí | Token de verificación GET |
| `WHATSAPP_APP_SECRET` | Recomendada | Validación de firma |

Webhook URL: `https://sistemataup.online/api/core/webhook/whatsapp` (nginx proxy `/api/core/` → `:3040`).

En modo `link`, los endpoints `/webhook/whatsapp` no verifican ni envían mensajes automáticamente.
