function initPrivateChat(otherUserId) {
  const socket = io();

  const messagesArea    = document.getElementById('messages-area');
  const messageInput    = document.getElementById('message-input');
  const sendBtn         = document.getElementById('send-btn');
  const typingIndicator = document.getElementById('typing-indicator');

  let typingTimeout = null;
  let isTyping = false;

  socket.on('connect', () => {
    console.log('Private chat connected. Socket ID:', socket.id);
  });

  socket.on('disconnect', (reason) => {
    if (reason === 'io server disconnect') socket.connect();
  });

  socket.on('new_private_message', (msg) => {
    const isThisConversation =
      (msg.sender_id === CONFIG.currentUserId && msg.receiver_id === otherUserId) ||
      (msg.sender_id === otherUserId && msg.receiver_id === CONFIG.currentUserId);

    if (isThisConversation) {
      if (!document.querySelector(`[data-msg-id="${msg.id}"]`)) {
        appendMessage(msg);
        scrollToBottom();
      }
    } else {
      showUnreadBadge(msg.sender_id);
    }
  });

  socket.on('user_typing', (data) => {
    if (data.user_id === otherUserId) {
      typingIndicator.style.display = 'block';
    }
  });

  socket.on('user_stop_typing', (data) => {
    if (data.user_id === otherUserId) {
      typingIndicator.style.display = 'none';
    }
  });

  socket.on('user_online', (data) => {
    if (data.user_id === otherUserId) {
      updateOnlineStatus(true);
    }
  });

  socket.on('user_offline', (data) => {
    if (data.user_id === otherUserId) {
      updateOnlineStatus(false);
    }
  });

  socket.on('error', (data) => {
    console.error('Server error:', data.message);
    alert(data.message);
  });

  function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) return;

    socket.emit('send_private_message', {
      receiver_id: otherUserId,
      content: content
    });

    messageInput.value = '';
    stopTyping();
  }

  sendBtn.addEventListener('click', sendMessage);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => {
    if (!isTyping) {
      isTyping = true;
      socket.emit('typing', { receiver_id: otherUserId });
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(stopTyping, 2000);
  });

  function stopTyping() {
    if (isTyping) {
      isTyping = false;
      socket.emit('stop_typing', { receiver_id: otherUserId });
    }
    clearTimeout(typingTimeout);
  }

  function appendMessage(msg) {
    const isOwn = msg.sender_id === CONFIG.currentUserId;

    const div = document.createElement('div');
    div.className = `message ${isOwn ? 'message-own' : ''}`;
    div.dataset.msgId = msg.id;

    div.innerHTML = `
      <img src="/static/uploads/${msg.sender_picture}"
           alt="${escapeHtml(msg.sender_username)}"
           class="avatar-sm message-avatar"
           onerror="this.src='/static/uploads/default.png'"/>
      <div class="message-body">
        <div class="message-meta">
          <span class="message-author">${escapeHtml(msg.sender_username)}</span>
          <span class="message-time">${msg.timestamp}</span>
          ${isOwn ? `<span class="read-status">${msg.is_read ? '✓✓' : '✓'}</span>` : ''}
        </div>
        <div class="message-content">${escapeHtml(msg.content)}</div>
      </div>
    `;

    messagesArea.appendChild(div);
  }

  function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  function updateOnlineStatus(isOnline) {
    const dot = document.querySelector('.online-dot');
    const subtitle = document.querySelector('.chat-subtitle');
    if (dot) {
      dot.classList.toggle('online', isOnline);
    }
    if (subtitle) {
      subtitle.textContent = isOnline ? 'Online' : 'Just went offline';
    }
  }

  function showUnreadBadge(senderId) {

    const sidebarLink = document.querySelector(
      `.sidebar-link[href="/chat/private/${senderId}"]`
    );
    if (sidebarLink) {
      let badge = sidebarLink.querySelector('.unread-badge');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'unread-badge badge badge-warning';
        badge.style.marginLeft = 'auto';
        sidebarLink.appendChild(badge);
      }
      badge.textContent = (parseInt(badge.textContent) || 0) + 1;
    }
  }

  scrollToBottom();
}