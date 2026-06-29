# Sistema de Alertas de Inversión con IA

Analiza ETFs y acciones USA con Claude + indicadores técnicos y te avisa por Telegram.

## Activos monitoreados
- VOO — ETF S&P 500
- QQQ — ETF Nasdaq 100
- AAPL — Apple
- MSFT — Microsoft

## Cuándo envía alertas
Solo cuando hay señal relevante:
- Claude recomienda COMPRAR
- RSI sobrevendido (<35) o sobrecomprado (>72)
- Movimiento del día ≥ 2.5%

Horario: lunes a viernes a las 17:00 UTC (12:00 Santiago)

---

## Paso 1 — Crear tu bot de Telegram (5 minutos)

1. Abre Telegram y busca `@BotFather`
2. Escribe `/newbot` y sigue las instrucciones
3. Copia el **token** que te da (formato: `123456789:AAHxxx...`)
4. Busca `@userinfobot` en Telegram, escríbele cualquier cosa
5. Copia tu **Chat ID** (número como `-123456789`)

---

## Paso 2 — Obtener API Key de Anthropic

1. Ve a https://console.anthropic.com
2. Settings → API Keys → Create Key
3. Copia la clave (formato: `sk-ant-...`)

---

## Paso 3 — Desplegar en Railway (gratis, 24/7)

1. Crea cuenta en https://railway.app (con GitHub)
2. New Project → Deploy from GitHub repo
3. Sube este código a un repo de GitHub primero, luego conéctalo
4. En Railway, ve a tu servicio → **Variables** y agrega:

```
TELEGRAM_TOKEN     = tu-token-del-bot
TELEGRAM_CHAT_ID   = tu-chat-id
ANTHROPIC_API_KEY  = sk-ant-...
```

5. Railway detecta el Dockerfile automáticamente y despliega.

**Plan gratuito de Railway:** $5 USD de crédito mensual gratis, suficiente para este bot liviano.

---

## Ejecutar localmente (para probar)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables (en tu terminal)
export TELEGRAM_TOKEN="tu-token"
export TELEGRAM_CHAT_ID="tu-chat-id"
export ANTHROPIC_API_KEY="sk-ant-..."

# Probar una sola vez (sin esperar el horario)
python -c "from src.analyzer import correr_analisis; correr_analisis()"

# Correr el scheduler completo
python main.py
```

---

## Agregar o quitar activos

Edita el diccionario `ACTIVOS` en `src/analyzer.py`:

```python
ACTIVOS = {
    "VOO":  "ETF S&P 500 (Vanguard)",
    "QQQ":  "ETF Nasdaq 100",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    # Agrega aquí más tickers de Yahoo Finance
    "AMZN": "Amazon",
    "VTI":  "ETF Total US Market",
}
```

---

## Ejemplo de alerta recibida en Telegram

```
🤖 Alerta de mercado — 15/06/2025 17:00
──────────────────────────────

📊 VOO — ETF S&P 500 (Vanguard)
💵 Precio: $521.40 (+0.8%)
📈 RSI: 32.1 | MACD: -1.23

SEÑAL: COMPRAR
RAZÓN: RSI en zona de sobreventa indica posible rebote. MACD converge hacia cruce alcista.
RIESGO: Bajo
CONSEJO: Buen momento para una compra parcial si tienes liquidez disponible.
```
