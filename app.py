from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from datetime import datetime
import pytz
import cv2
import os

app = Flask(__name__)
CORS(app)

# ⚠️ Credenziali Telegram
TELEGRAM_BOT_TOKEN = "7827685878:AAGo7ijMFJXrRGRTrXNxw7fLDHhKwbYLqDQ"
TELEGRAM_CHAT_ID = "7096713514"

# Variabile globale per la webcam
camera = None

# 🌐 URL pubblico del server (Render imposta automaticamente questa variabile)
SERVER_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000").rstrip("/")


def send_telegram_message(message):
    """Invia un messaggio al bot Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"❌ Errore nell'invio del messaggio Telegram: {e}")
        return None


def get_client_ip(request):
    """Ottiene l'IP reale del client considerando i proxy"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


# --------------------------
# SEZIONE VIDEO LIVE
# --------------------------

def generate_frames():
    """Genera i frame video dalla webcam e li invia in streaming"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)  # Usa la webcam predefinita

    while True:
        success, frame = camera.read()
        if not success:
            print("⚠️ Nessun frame catturato.")
            break
        else:
            # Stampa su console l'orario del frame catturato
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Frame catturato")

            # Converti il frame in JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Restituisci il frame come parte dello stream MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video')
def video_feed():
    """Ritorna lo streaming video in tempo reale"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# --------------------------
# SEZIONE TRACKING E HOME
# --------------------------

@app.route('/')
def home():
    """Home del sito — invia link camera via Telegram"""
    client_ip = get_client_ip(request)
    italy_tz = pytz.timezone('Europe/Rome')
    now = datetime.now(italy_tz)
    timestamp = now.strftime("%d/%m/%Y alle %H:%M:%S")

    video_link = f"{SERVER_URL}/video"

    message = f"""
🎯 <b>Nuovo Accesso al Sito!</b>

🕐 <b>Data e Ora:</b> {timestamp}
🌐 <b>Indirizzo IP:</b> {client_ip}
🎥 <b>Live Camera:</b> <a href="{video_link}">{video_link}</a>
"""

    send_telegram_message(message)

    return jsonify({
        "status": "online",
        "message": "Benvenuto nel Backend Streaming Hub!",
        "video_link": video_link
    })


@app.route('/track-click', methods=['POST'])
def track_click():
    """Riceve i click e invia notifica Telegram"""
    try:
        data = request.get_json()
        platform = data.get('platform', 'Sconosciuta')

        client_ip = get_client_ip(request)
        italy_tz = pytz.timezone('Europe/Rome')
        now = datetime.now(italy_tz)
        timestamp = now.strftime("%d/%m/%Y alle %H:%M:%S")

        message = f"""
🎬 <b>Nuovo Click Rilevato!</b>

📱 <b>Piattaforma:</b> {platform}
🕐 <b>Data e Ora:</b> {timestamp}
🌐 <b>Indirizzo IP:</b> {client_ip}
"""

        send_telegram_message(message)

        return jsonify({"success": True, "message": "Notifica inviata con successo"}), 200

    except Exception as e:
        print(f"❌ Errore: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Server attivo su porta {port}")
    print(f"🌍 URL pubblico: {SERVER_URL}")
    print("🎥 Stream disponibile su /video")
    app.run(host='0.0.0.0', port=port, debug=True)
