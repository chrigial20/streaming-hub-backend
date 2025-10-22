from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)  # Permette richieste da Netlify

# ⚠️ Le tue credenziali Telegram
TELEGRAM_BOT_TOKEN = "7827685878:AAGo7ijMFJXrRGRTrXNxw7fLDHhKwbYLqDQ"
TELEGRAM_CHAT_ID = "7096713514"

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
        print(f"Errore nell'invio del messaggio Telegram: {e}")
        return None

def get_client_ip(request):
    """Ottiene l'IP reale del client considerando i proxy"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Backend Streaming Hub attivo!"
    })

@app.route('/track-click', methods=['POST'])
def track_click():
    """Riceve i click e invia notifica Telegram"""
    try:
        data = request.get_json()
        platform = data.get('platform', 'Sconosciuta')
        
        # Ottieni informazioni
        client_ip = get_client_ip(request)
        
        # Data e ora in formato italiano (timezone Europa/Roma)
        italy_tz = pytz.timezone('Europe/Rome')
        now = datetime.now(italy_tz)
        timestamp = now.strftime("%d/%m/%Y alle %H:%M:%S")
        
        # Crea il messaggio per Telegram
        message = f"""
🎬 <b>Nuovo Click Rilevato!</b>

📱 <b>Piattaforma:</b> {platform}
🕐 <b>Data e Ora:</b> {timestamp}
🌐 <b>Indirizzo IP:</b> {client_ip}
"""
        
        # Invia notifica Telegram
        telegram_response = send_telegram_message(message)
        
        if telegram_response and telegram_response.get('ok'):
            return jsonify({
                "success": True,
                "message": "Notifica inviata con successo"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Errore nell'invio della notifica"
            }), 500
            
    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Per sviluppo locale
    app.run(host='0.0.0.0', port=5000, debug=True)