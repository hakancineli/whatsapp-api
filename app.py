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

# Tüm mesajları getir
@app.route('/messages/all', methods=['GET'])
def get_all_messages():
    try:
        print('Tüm mesajlar isteniyor...')
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        # Son 1 ay için tarih hesapla
        bir_ay_once = datetime.now() - timedelta(days=30)
        bir_ay_once_str = bir_ay_once.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        print('API isteği yapılıyor:', f"{API_URL}/api/v1/messages?after={bir_ay_once_str}")
        print('Headers:', headers)
        
        # Messages API'yi çağır
        response = requests.get(
            f"{API_URL}/api/v1/messages?after={bir_ay_once_str}",
            headers=headers
        )
        
        print('API yanıt durumu:', response.status_code)
        
        if response.status_code == 200:
            data = response.json()
            print("API Yanıtı:", json.dumps(data, indent=2))
            
            if 'messages' in data and isinstance(data['messages'], list):
                print(f"Toplam mesaj sayısı: {len(data['messages'])}")
                text_messages = [msg for msg in data['messages'] if msg.get('type') == 'text' and msg.get('text', {}).get('body')]
                print(f"Text mesaj sayısı: {len(text_messages)}")
            
            return jsonify(data), 200
        else:
            error_message = f"API Hatası: Status Code {response.status_code}"
            try:
                error_data = response.json()
                error_message += f", Response: {json.dumps(error_data)}"
            except:
                error_message += f", Response Text: {response.text}"
            
            print(error_message)
            return jsonify({"error": "Mesajlar alınamadı", "details": error_message}), response.status_code
            
    except Exception as e:
        error_message = f"Hata: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.json
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({"error": "Telefon numarası ve mesaj zorunludur"}), 400

        # WhatsApp API'ye istek gönder
        headers = {
            "D360-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        print('Mesaj gönderiliyor:', payload)
        print('Headers:', headers)
        
        response = requests.post(
            f"{API_URL}/messages",
            headers=headers,
            json=payload
        )
        
        print('API yanıt durumu:', response.status_code)
        print('API yanıt başlıkları:', response.headers)
        print('API yanıt içeriği:', response.text)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            error_message = f"API Hatası: Status Code {response.status_code}"
            try:
                error_data = response.json()
                error_message += f", Response: {json.dumps(error_data)}"
            except:
                error_message += f", Response Text: {response.text}"
            
            print(error_message)
            return jsonify({"error": "Mesaj gönderilemedi", "details": error_message}), response.status_code
        
    except Exception as e:
        error_message = f"Hata: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        # Gelen mesajları işle
        print("Gelen webhook verisi:", json.dumps(data, indent=2))
        return jsonify({"status": "success"}), 200
    except Exception as e:
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
            f"{API_URL}/api/v1/configs/webhook",
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
            f"{API_URL}/api/v1/configs/webhook",
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
            f"{API_URL}/channels",
            headers=headers
        )
        print('Channels yanıt durumu:', channels_response.status_code)
        print('Channels yanıt içeriği:', channels_response.text)
        
        # Sonra contacts endpoint'ini test edelim
        print('\nContacts testi yapılıyor...')
        contacts_response = requests.get(
            f"{API_URL}/contacts",
            headers=headers
        )
        print('Contacts yanıt durumu:', contacts_response.status_code)
        print('Contacts yanıt içeriği:', contacts_response.text)
        
        # Son olarak messages endpoint'ini test edelim
        print('\nMessages testi yapılıyor...')
        messages_response = requests.get(
            f"{API_URL}/messages",
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 