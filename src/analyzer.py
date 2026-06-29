import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
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
    df = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
    if df.empty or len(df) < 20:
        return None

    close = df["Close"].squeeze()

    rsi_series = ta.rsi(close, length=14)
    macd_obj   = ta.macd(close, fast=12, slow=26, signal=9)
    sma20      = ta.sma(close, length=20)
    sma50      = ta.sma(close, length=50)

    rsi   = round(float(rsi_series.iloc[-1]),   1) if rsi_series   is not None else None
    macd_line   = round(float(macd_obj["MACD_12_26_9"].iloc[-1]),   4) if macd_obj is not None else None
    macd_signal = round(float(macd_obj["MACDs_12_26_9"].iloc[-1]),  4) if macd_obj is not None else None
    sma20_val   = round(float(sma20.iloc[-1]),  2) if sma20 is not None else None
    sma50_val   = round(float(sma50.iloc[-1]),  2) if sma50 is not None else None

    precio_actual = round(float(close.iloc[-1]), 2)
    precio_ayer   = round(float(close.iloc[-2]), 2)
    cambio_pct    = round((precio_actual - precio_ayer) / precio_ayer * 100, 2)

    return {
        "ticker":        ticker,
        "precio":        precio_actual,
        "cambio_pct":    cambio_pct,
        "rsi":           rsi,
        "macd":          macd_line,
        "macd_signal":   macd_signal,
        "sma20":         sma20_val,
        "sma50":         sma50_val,
    }


def analizar_con_claude(datos: dict, nombre: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Eres un asesor financiero conservador para un inversor chileno principiante con menos de $500 USD.

Analiza este activo y da una recomendación clara: COMPRAR, MANTENER o ESPERAR (no vender agresivamente).

Activo: {datos['ticker']} - {nombre}
Precio actual: ${datos['precio']} USD
Cambio hoy: {datos['cambio_pct']}%
RSI (14): {datos['rsi']} (sobrecomprado >70, sobrevendido <30)
MACD: {datos['macd']} | Señal MACD: {datos['macd_signal']}
SMA 20 días: {datos['sma20']} | SMA 50 días: {datos['sma50']}

Responde en español, máximo 4 líneas. Formato:
SEÑAL: [COMPRAR / MANTENER / ESPERAR]
RAZÓN: [1-2 oraciones explicando por qué]
RIESGO: [Bajo / Medio / Alto]
CONSEJO: [Una acción concreta para el inversor]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def enviar_telegram(mensaje: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
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
        print(f"[{hora}] Sin señales relevantes. No se envió mensaje.")


if __name__ == "__main__":
    correr_analisis()
