import os
import yfinance as yf
import pandas as pd
import ta
import anthropic
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

ACTIVOS = {
    "VOO":  "ETF S&P 500 (Vanguard)",
    "QQQ":  "ETF Nasdaq 100",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
}

def obtener_datos(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="3mo", interval="1d")
        if df.empty or len(df) < 20:
            return None

        close = df["Close"].squeeze()

        rsi   = round(float(ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]), 1)
        macd_obj = ta.trend.MACD(close)
        macd_line   = round(float(macd_obj.macd().iloc[-1]), 4)
        macd_signal = round(float(macd_obj.macd_signal().iloc[-1]), 4)
        sma20 = round(float(ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1]), 2)
        sma50 = round(float(ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1]), 2)

        precio_actual = round(float(close.iloc[-1]), 2)
        precio_ayer   = round(float(close.iloc[-2]), 2)
        cambio_pct    = round((precio_actual - precio_ayer) / precio_ayer * 100, 2)

        return {
            "ticker":      ticker,
            "precio":      precio_actual,
            "cambio_pct":  cambio_pct,
            "rsi":         rsi,
            "macd":        macd_line,
            "macd_signal": macd_signal,
            "sma20":       sma20,
            "sma50":       sma50,
        }
    except Exception as e:
        print(f"Error obteniendo {ticker}: {e}")
        return None


def analizar_con_claude(datos: dict, nombre: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Eres un asesor financiero conservador para un inversor chileno principiante con menos de $500 USD.

Analiza este activo y da una recomendación clara: COMPRAR, MANTENER o ESPERAR.

Activo: {datos['ticker']} - {nombre}
Precio actual: ${datos['precio']} USD
Cambio hoy: {datos['cambio_pct']}%
RSI (14): {datos['rsi']} (sobrecomprado >70, sobrevendido <30)
MACD: {datos['macd']} | Señal MACD: {datos['macd_signal']}
SMA 20 días: {datos['sma20']} | SMA 50 días: {datos['sma50']}

Responde en español, máximo 4 líneas. Formato:
SEÑAL: [COMPRAR / MANTENER / ESPERAR]
RAZÓN: [1-2 oraciones]
RIESGO: [Bajo / Medio / Alto]
CONSEJO: [Una acción concreta]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def enviar_telegram(mensaje: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()


def es_senal_relevante(datos: dict, analisis: str) -> bool:
    if "COMPRAR" in analisis:
        return True
    if datos["rsi"] and (datos["rsi"] < 35 or datos["rsi"] > 72):
        return True
    if abs(datos["cambio_pct"]) >= 2.5:
        return True
    return False


def correr_analisis():
    hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    alertas = []

    for ticker, nombre in ACTIVOS.items():
        datos = obtener_datos(ticker)
        if not datos:
            print(f"Sin datos para {ticker}, saltando.")
            continue
        analisis = analizar_con_claude(datos, nombre)
        if es_senal_relevante(datos, analisis):
            bloque = (
                f"📊 *{ticker}* — {nombre}\n"
                f"💵 Precio: ${datos['precio']} ({'+' if datos['cambio_pct'] >= 0 else ''}{datos['cambio_pct']}%)\n"
                f"📈 RSI: {datos['rsi']} | MACD: {datos['macd']}\n\n"
                f"{analisis}"
            )
            alertas.append(bloque)

    if alertas:
        encabezado = f"🤖 *Alerta de mercado* — {hora}\n{'─'*30}\n\n"
        mensaje = encabezado + "\n\n──────────\n\n".join(alertas)
        enviar_telegram(mensaje)
        print(f"[{hora}] {len(alertas)} alerta(s) enviadas.")
    else:
        print(f"[{hora}] Sin señales relevantes.")


if __name__ == "__main__":
    correr_analisis()

