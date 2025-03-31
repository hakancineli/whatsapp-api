# WhatsApp API Uygulaması

Bu uygulama, 360dialog WhatsApp API'sini kullanarak mesaj gönderme ve alma işlemlerini gerçekleştirir.

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyasını düzenleyin:
- `DIALOG_API_KEY` değerini 360dialog'dan aldığınız API anahtarı ile değiştirin.

3. Uygulamayı çalıştırın:
```bash
python app.py
```

## API Endpointleri

### Mesaj Gönderme
- **POST** `/send-message`
- Body:
```json
{
    "phone_number": "905xxxxxxxxx",
    "message": "Merhaba!"
}
```

### Webhook
- **POST** `/webhook`
- Gelen mesajları işlemek için kullanılır.

### Webhook Güncelleme
- **POST** `/update-webhook`
- Body:
```json
{
    "url": "https://your-domain.com/webhook"
}
```

### Webhook Durumu Kontrolü
- **GET** `/check-webhook`

## Notlar
- Telefon numaraları uluslararası formatta olmalıdır (örn: 905xxxxxxxxx)
- Sandbox ortamında test edilmektedir 