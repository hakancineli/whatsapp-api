document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const messageList = document.querySelector('.message-list');
    const chatList = document.querySelector('.chat-list');
    let selectedChat = null;
    let lastMessageTimestamp = null;

    // Mesaj zamanını formatla
    function formatMessageTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
            // Bugün
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (days === 1) {
            // Dün
            return 'Dün';
        } else if (days < 7) {
            // Son 7 gün
            const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
            return days[date.getDay()];
        } else {
            // Daha eski
            return `${date.getDate().toString().padStart(2, '0')}.${(date.getMonth() + 1).toString().padStart(2, '0')}.${date.getFullYear()}`;
        }
    }

    // Telefon numarasını formatla
    function formatPhoneNumber(phone) {
        if (!phone) return 'Bilinmeyen';
        return phone.replace(/(\d{2})(\d{3})(\d{3})(\d{4})/, '+$1 $2 $3 $4');
    }

    // Sohbet başlığını güncelle
    function updateChatHeader(chat) {
        const userNameElement = document.querySelector('.user-name h3');
        if (userNameElement && chat) {
            userNameElement.textContent = chat.name;
        }
    }

    // Mesajları göster
    function renderMessages(messages) {
        if (!messages || messages.length === 0) {
            messageList.innerHTML = '<div class="no-messages">Henüz mesaj yok</div>';
            return;
        }

        messageList.innerHTML = messages.map(msg => `
            <div class="message ${msg.type}">
                <div class="message-content">
                    ${msg.text}
                    <span class="message-time">${msg.time}</span>
                </div>
            </div>
        `).join('');
        messageList.scrollTop = messageList.scrollHeight;
    }

    // Mesajları yükle
    async function loadMessages(chat) {
        try {
            const response = await fetch('/test-messages');
            if (response.ok) {
                const data = await response.json();
                console.log('API Yanıtı:', data);

                if (data.messages_data && data.messages_data.messages) {
                    // Seçili sohbete ait mesajları filtrele
                    const chatMessages = data.messages_data.messages.filter(msg => 
                        (msg.from === chat.phone || msg.to === chat.phone) && 
                        msg.type === 'text' && 
                        msg.text && 
                        msg.text.body
                    );

                    // Mesajları tarihe göre sırala
                    const sortedMessages = chatMessages.sort((a, b) => 
                        new Date(a.timestamp) - new Date(b.timestamp)
                    );

                    // Mesajları formatla
                    const formattedMessages = sortedMessages.map(msg => ({
                        text: msg.text.body,
                        type: msg.from === chat.phone ? 'received' : 'sent',
                        time: formatMessageTime(msg.timestamp),
                        timestamp: msg.timestamp
                    }));

                    chat.messages = formattedMessages;
                    renderMessages(chat.messages);
                }
            }
        } catch (error) {
            console.error('Mesajlar yüklenirken hata:', error);
        }
    }

    // Sohbet seç
    function selectChat(chat) {
        selectedChat = chat;
        updateChatHeader(chat);
        loadMessages(chat);
        
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.phone === chat.phone) {
                item.classList.add('active');
            }
        });
    }

    // Tüm sohbetleri yükle
    async function loadChats() {
        try {
            console.log('Sohbetler yükleniyor...');
            const response = await fetch('/test-messages');
            console.log('API yanıt durumu:', response.status);
            const data = await response.json();
            console.log('API yanıtı:', data);

            if (!data.messages_data || !data.messages_data.messages) {
                console.error('Mesajlar alınamadı veya yanlış format:', data);
                return;
            }

            const messages = data.messages_data.messages;
            console.log('Toplam mesaj sayısı:', messages.length);

            // Mesajları numaralarına göre grupla
            const chatGroups = {};
            messages.forEach(msg => {
                if (msg.type !== 'text' || !msg.text || !msg.text.body) return;
                
                const number = msg.from || msg.to;
                if (!chatGroups[number]) {
                    chatGroups[number] = {
                        phone: number,
                        messages: [],
                        lastMessage: null,
                        time: null
                    };
                }
                chatGroups[number].messages.push(msg);
            });

            console.log('Sohbet grupları:', chatGroups);

            // Her grup için son mesajı ve zamanı belirle
            const chats = Object.values(chatGroups).map(group => {
                const sortedMessages = group.messages.sort((a, b) => 
                    new Date(b.timestamp) - new Date(a.timestamp)
                );
                const lastMsg = sortedMessages[0];
                return {
                    phone: group.phone,
                    name: formatPhoneNumber(group.phone),
                    lastMessage: lastMsg.text.body,
                    time: formatMessageTime(lastMsg.timestamp),
                    messages: sortedMessages,
                    unread: 0
                };
            });

            // Sohbetleri son mesaj zamanına göre sırala
            chats.sort((a, b) => {
                const timeA = new Date(a.messages[0].timestamp);
                const timeB = new Date(b.messages[0].timestamp);
                return timeB - timeA;
            });

            console.log('İşlenmiş sohbetler:', chats);

            // Sohbet listesini güncelle
            chatList.innerHTML = '';
            
            if (chats.length === 0) {
                chatList.innerHTML = '<div class="no-chats">Henüz sohbet yok</div>';
                return;
            }

            chats.forEach(chat => {
                const chatElement = document.createElement('div');
                chatElement.className = 'chat-item';
                chatElement.dataset.phone = chat.phone;
                chatElement.innerHTML = `
                    <div class="chat-item-content">
                        <div class="chat-item-title">${chat.name}</div>
                        <div class="chat-item-message">${chat.lastMessage}</div>
                    </div>
                    <div class="chat-item-time">${chat.time}</div>
                `;
                
                chatElement.addEventListener('click', () => selectChat(chat));
                chatList.appendChild(chatElement);
            });

            // İlk sohbeti seç
            if (chats.length > 0 && !selectedChat) {
                selectChat(chats[0]);
            }

        } catch (error) {
            console.error('Sohbetler yüklenirken hata:', error);
        }
    }

    // Mesaj gönder
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (message && selectedChat) {
            try {
                const response = await fetch('/send-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        phone_number: selectedChat.phone,
                        message: message
                    })
                });

                if (response.ok) {
                    const now = new Date();
                    const newMessage = {
                        text: message,
                        type: 'sent',
                        time: formatMessageTime(now),
                        timestamp: now.toISOString()
                    };

                    selectedChat.messages.push(newMessage);
                    selectedChat.lastMessage = message;
                    selectedChat.time = formatMessageTime(now);

                    renderMessages(selectedChat.messages);
                    messageInput.value = '';
                    await loadChats(); // Sohbet listesini güncelle
                } else {
                    const errorData = await response.json();
                    console.error('Mesaj gönderme hatası:', errorData);
                    alert('Mesaj gönderilemedi');
                }
            } catch (error) {
                console.error('Mesaj gönderilirken hata:', error);
                alert('Mesaj gönderilirken bir hata oluştu');
            }
        } else if (!selectedChat) {
            alert('Lütfen bir sohbet seçin');
        }
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Başlangıçta sohbetleri yükle
    loadChats();

    // Her 30 saniyede bir sohbetleri güncelle
    setInterval(loadChats, 30000);
}); 