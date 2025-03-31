from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
CORS(app)

# 360dialog API bilgileri
API_KEY = os.getenv('DIALOG_API_KEY')
API_URL = os.getenv('API_URL')

# Mesajları saklamak için basit bir veritabanı sistemi
MESSAGES_FILE = 'messages.json'

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'messages': []}

def save_messages(messages):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# Tüm mesajları getir
@app.route('/messages', methods=['GET'])
def get_all_messages():
    try:
        messages_data = load_messages()
        return jsonify(messages_data)
    except Exception as e:
        print("Mesajları alma hatası:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.json
        phone_number = data.get('phone')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({"error": "Telefon numarası ve mesaj gerekli"}), 400
            
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        response = requests.post(
            f"{API_URL}/v1/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            # Gönderilen mesajı kaydet
            messages_data = load_messages()
            new_message = {
                'id': response.json().get('messages', [{}])[0].get('id', ''),
                'to': phone_number,
                'text': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'outgoing'
            }
            messages_data['messages'].append(new_message)
            save_messages(messages_data)
            
            return jsonify({
                'status': 'success',
                'message': 'Mesaj başarıyla gönderildi',
                'data': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Mesaj gönderilemedi: {response.text}'
            }), response.status_code
            
    except Exception as e:
        print('Hata:', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("Gelen webhook verisi:", json.dumps(data, indent=2))
        
        # Mesajları yükle
        messages_data = load_messages()
        
        # Mesaj tipini kontrol et
        if 'messages' in data:
            for message in data['messages']:
                # Yeni mesajı ekle
                new_message = {
                    'id': message.get('id'),
                    'from': message.get('from'),
                    'text': message.get('text', {}).get('body', ''),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'incoming'
                }
                messages_data['messages'].append(new_message)
                
                print(f"Mesaj ID: {new_message['id']}")
                print(f"Gönderen: {new_message['from']}")
                print(f"Mesaj: {new_message['text']}")
                print("------------------------")
        
        # Mesajları kaydet
        save_messages(messages_data)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Webhook hatası:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/update-webhook', methods=['POST'])
def update_webhook():
    try:
        data = request.json
        webhook_url = data.get('url')
        
        if not webhook_url:
            return jsonify({"error": "Webhook URL zorunludur"}), 400

        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": webhook_url
        }
        
        response = requests.post(
            f"{API_URL}/v1/configs/webhook",
            headers=headers,
            json=payload
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check-webhook', methods=['GET'])
def check_webhook():
    try:
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{API_URL}/v1/configs/webhook",
            headers=headers
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-messages', methods=['GET'])
def test_messages():
    try:
        print('Test: Son mesajlar kontrol ediliyor...')
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        # Önce channels endpoint'ini test edelim
        print('\nChannels testi yapılıyor...')
        channels_response = requests.get(
            f"{API_URL}/v1/channels",
            headers=headers
        )
        print('Channels yanıt durumu:', channels_response.status_code)
        print('Channels yanıt içeriği:', channels_response.text)
        
        # Sonra contacts endpoint'ini test edelim
        print('\nContacts testi yapılıyor...')
        contacts_response = requests.get(
            f"{API_URL}/v1/contacts",
            headers=headers
        )
        print('Contacts yanıt durumu:', contacts_response.status_code)
        print('Contacts yanıt içeriği:', contacts_response.text)
        
        # Son olarak messages endpoint'ini test edelim
        print('\nMessages testi yapılıyor...')
        messages_response = requests.get(
            f"{API_URL}/v1/messages",
            headers=headers
        )
        print('Messages yanıt durumu:', messages_response.status_code)
        print('Messages yanıt içeriği:', messages_response.text)
        
        # Tüm sonuçları döndür
        return jsonify({
            "channels_status": channels_response.status_code,
            "channels_data": channels_response.json() if channels_response.status_code == 200 else None,
            "contacts_status": contacts_response.status_code,
            "contacts_data": contacts_response.json() if contacts_response.status_code == 200 else None,
            "messages_status": messages_response.status_code,
            "messages_data": messages_response.json() if messages_response.status_code == 200 else None
        }), 200
            
    except Exception as e:
        error_message = f"Hata: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/test-api')
def test_api():
    try:
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        print('API testi yapılıyor...')
        print('API URL:', API_URL)
        print('Headers:', headers)
        
        # Messages API'yi çağır
        response = requests.get(
            f"{API_URL}/v1/messages",
            headers=headers
        )
        
        print('API yanıt durumu:', response.status_code)
        print('API yanıtı:', response.text)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'data': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'API Hatası: Status Code {response.status_code}, Response: {response.text}'
            }), response.status_code
            
    except Exception as e:
        print('Hata:', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/setup-webhook', methods=['POST'])
def setup_webhook():
    try:
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        # Webhook URL'sini al (örnek: https://your-domain.com/webhook)
        webhook_url = request.json.get('url')
        if not webhook_url:
            return jsonify({"error": "Webhook URL gerekli"}), 400
            
        payload = {
            "url": webhook_url,
            "enabled": True
        }
        
        print('Webhook ayarlanıyor:', payload)
        print('Headers:', headers)
        
        response = requests.post(
            f"{API_URL}/v1/configs/webhook",
            headers=headers,
            json=payload
        )
        
        print('API yanıt durumu:', response.status_code)
        print('API yanıtı:', response.text)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Webhook başarıyla ayarlandı',
                'data': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Webhook ayarlanamadı: {response.text}'
            }), response.status_code
            
    except Exception as e:
        print('Hata:', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 