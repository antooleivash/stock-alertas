import schedule
import time
from src.analyzer import correr_analisis

def job():
    try:
        correr_analisis()
    except Exception as e:
        print(f"Error en análisis: {e}")

schedule.every().monday.at("17:00").do(job)
schedule.every().tuesday.at("17:00").do(job)
schedule.every().wednesday.at("17:00").do(job)
schedule.every().thursday.at("17:00").do(job)
schedule.every().friday.at("17:00").do(job)

print("Scheduler activo. Analizando mercado lunes a viernes a las 17:00 UTC-5...")

while True:
    schedule.run_pending()
    time.sleep(60)
