from flask import current_app                         
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio, db
from app.models import Room, RoomMessage, PrivateMessage, User
from datetime import datetime, timezone
import functools


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            from flask_socketio import disconnect
            disconnect()
            return
        return f(*args, **kwargs)
    return wrapped


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        current_user.is_online = True
        db.session.commit()
        emit('user_online', {
            'user_id': current_user.id,
            'username': current_user.username
        }, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        current_user.is_online = False
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        emit('user_offline', {
            'user_id': current_user.id,
            'username': current_user.username
        }, broadcast=True)


@socketio.on('join_room')
@authenticated_only
def handle_join_room(data):
    room_id = data.get('room_id')
    current_app.logger.debug(f'join_room event room_id={room_id} user_id={current_user.id}')
    if not room_id:
        return

    room = db.session.get(Room, room_id)
    if not room:
        return

    socketio_room = f'room_{room_id}'
    join_room(socketio_room)
    emit('user_joined_room', {
        'username': current_user.username,
        'user_id': current_user.id,
        'member_count': room.member_count
    }, to=socketio_room)


@socketio.on('leave_room')
@authenticated_only
def handle_leave_room(data):
    room_id = data.get('room_id')
    if not room_id:
        return

    socketio_room = f'room_{room_id}'
    leave_room(socketio_room)

    room = db.session.get(Room, room_id)
    if room:
        emit('user_left_room', {
            'username': current_user.username,
            'user_id': current_user.id,
            'member_count': room.member_count
        }, to=socketio_room)


@socketio.on('send_room_message')
@authenticated_only
def handle_room_message(data):
    room_id = data.get('room_id')
    content = data.get('content', '').strip()
    current_app.logger.debug(f'send_room_message event room_id={room_id} user_id={current_user.id}')

    if not room_id or not content:
        return

    if len(content) > 2000:
        emit('error', {'message': 'Message too long (max 2000 characters).'})
        return

    room = db.session.get(Room, room_id)
    if not room:
        return

    message = RoomMessage(
        room_id=room_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    socketio_room = f'room_{room_id}'
    emit('new_room_message', message.to_dict(), to=socketio_room)


@socketio.on('send_private_message')
@authenticated_only
def handle_private_message(data):
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()

    if not receiver_id or not content:
        return

    if len(content) > 2000:
        emit('error', {'message': 'Message too long.'})
        return

    if receiver_id == current_user.id:
        return

    receiver = db.session.get(User, receiver_id)
    if not receiver:
        return

    message = PrivateMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        is_read=False
    )
    db.session.add(message)
    db.session.commit()

    msg_dict = message.to_dict()
    emit('new_private_message', msg_dict, to=f'user_{current_user.id}')  
    emit('new_private_message', msg_dict, to=f'user_{receiver_id}')       


@socketio.on('typing')
@authenticated_only
def handle_typing(data):
    if 'receiver_id' in data:
        emit('user_typing', {
            'user_id': current_user.id,
            'username': current_user.username
        }, to=f"user_{data['receiver_id']}")
    elif 'room_id' in data:
        emit('user_typing', {
            'user_id': current_user.id,
            'username': current_user.username
        }, to=f"room_{data['room_id']}")


@socketio.on('stop_typing')
@authenticated_only
def handle_stop_typing(data):
    if 'receiver_id' in data:
        emit('user_stop_typing', {
            'user_id': current_user.id
        }, to=f"user_{data['receiver_id']}")
    elif 'room_id' in data:
        emit('user_stop_typing', {
            'user_id': current_user.id
        }, to=f"room_{data['room_id']}")