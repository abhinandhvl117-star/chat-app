function initRoomChat(roomId) {

  const socket = io();

  const messagesArea  = document.getElementById('messages-area');
  const messageInput  = document.getElementById('message-input');
  const sendBtn       = document.getElementById('send-btn');
  const memberCount   = document.getElementById('member-count');
  const typingIndicator = document.getElementById('typing-indicator');
  const typingText    = document.getElementById('typing-text');

  const typingUsers = {};
  let typingTimeout = null;

  socket.on('connect', () => {
    console.log('Connected to SocketIO server. Socket ID:', socket.id, 'roomId:', roomId);

    socket.emit('join_room', { room_id: roomId });
  });

  socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
    if (reason === 'io server disconnect') {
      socket.connect();
    }
  });

  socket.on('connect_error', (err) => {
    console.error('Connection error:', err.message);
  });

  socket.on('user_joined_room', (data) => {
    if (memberCount) {
      memberCount.textContent = `${data.member_count} members`;
    }
    if (data.user_id !== CONFIG.currentUserId) {
      appendSystemMessage(`${data.username} joined the room.`);
    }
  });

  socket.on('user_left_room', (data) => {
    if (memberCount) {
      memberCount.textContent = `${data.member_count} members`;
    }
    if (data.user_id !== CONFIG.currentUserId) {
      appendSystemMessage(`${data.username} left the room.`);
    }
  });

  socket.on('new_room_message', (msg) => {
    console.log('Received new_room_message', msg);
    appendMessage(msg);
    scrollToBottom();
  });

  socket.on('user_typing', (data) => {
    if (data.user_id === CONFIG.currentUserId) return;
    typingUsers[data.user_id] = data.username;
    updateTypingIndicator();
  });

  socket.on('user_stop_typing', (data) => {
    delete typingUsers[data.user_id];
    updateTypingIndicator();
  });

  socket.on('error', (data) => {
    console.error('Server error:', data.message);
    alert(data.message);
  });

  function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) return;
    
    console.log('Sending room message', { room_id: roomId, content });
    socket.emit('send_room_message', {
      room_id: roomId,
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
    socket.emit('typing', { room_id: roomId });

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(stopTyping, 2000);
  });

  function stopTyping() {
    socket.emit('stop_typing', { room_id: roomId });
    clearTimeout(typingTimeout);
  }

  function updateTypingIndicator() {
    if (!typingIndicator || !typingText) return;
    const names = Object.values(typingUsers);
    if (names.length === 0) {
      typingIndicator.style.display = 'none';
      typingText.textContent = '';
    } else if (names.length === 1) {
      typingText.textContent = `${names[0]} is typing…`;
      typingIndicator.style.display = 'block';
    } else {
      typingText.textContent = `${names.join(', ')} are typing…`;
      typingIndicator.style.display = 'block';
    }
  }

  function appendMessage(msg) {
    const isOwn = msg.user_id === CONFIG.currentUserId;

    const div = document.createElement('div');
    div.className = `message ${isOwn ? 'message-own' : ''}`;
    div.dataset.msgId = msg.id;

    div.innerHTML = `
      <img src="/static/uploads/${msg.profile_picture}"
           alt="${escapeHtml(msg.username)}"
           class="avatar-sm message-avatar"
           onerror="this.src='/static/uploads/default.png'"/>
      <div class="message-body">
        <div class="message-meta">
          <a href="/profile/${escapeHtml(msg.username)}" class="message-author">
            ${escapeHtml(msg.username)}
          </a>
          <span class="message-time">${msg.timestamp}</span>
        </div>
        <div class="message-content">${escapeHtml(msg.content)}</div>
      </div>
    `;

    messagesArea.appendChild(div);
  }

  function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'system-message';
    div.style.cssText = 'text-align:center;color:var(--text-muted);font-size:0.78rem;padding:0.3rem;';
    div.textContent = text;
    messagesArea.appendChild(div);
    scrollToBottom();
  }

  function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  scrollToBottom();
  window.addEventListener('beforeunload', () => {
    socket.emit('leave_room', { room_id: roomId });
  });
}