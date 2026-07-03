from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.chat import chat_bp
from app.models import Room, RoomMessage, PrivateMessage, User
from app.extensions import  db

@chat_bp.route('/rooms')
@login_required
def rooms():
    all_rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template('chat/rooms.html', rooms=all_rooms, title='Chat Rooms')

@chat_bp.route('/rooms/create', methods=['GET', 'POST'])
@login_required
def create_room():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Room name is required.', 'danger')
            return redirect(url_for('chat.rooms'))
        
        if len(name) > 100:
            flash('Room name must be under 100 characters.', 'danger')
            return redirect(url_for('chat.rooms'))
        
        # check duplicate room name
        existing = Room.query.filter_by(name=name).first()
        if existing:
            flash('A room with that name already exists.', 'warning')
            return redirect(url_for('chat.room', room_id=existing.id))
        
        room = Room(
            name=name,
            description=description,
            created_by=current_user.id 
        )
        db.session.add(room)
        db.session.commit()
        
        # auto join the group that the user just created
        room.members.append(current_user)
        db.session.commit()
        
        flash(f'Room "{name}" created.', 'success')
        return redirect(url_for('chat.room', room_id=room.id))
    
    return render_template(
        'chat/rooms.html',
        rooms=Room.query.order_by(Room.created_at.desc()).all(),
        show_create=True,
        title='Create Room'
    )
    
@chat_bp.route('/room/<int:room_id>')
@login_required
def room(room_id):
    chat_room = Room.query.get_or_404(room_id)
    
    if not chat_room.members.filter_by(id=current_user.id).first():
        chat_room.members.append(current_user)
        db.session.commit()
        
    messages = RoomMessage.query.filter_by(room_id=room_id)\
        .order_by(RoomMessage.timestamp.asc())\
        .limit(50).all()
        
        
    return render_template(
        'chat/room.html',
        room=chat_room,
        messages=messages,
        title=f'#{chat_room.name}'
    )
    
@chat_bp.route('/room/<int:room_id>/leave', methods=['POST'])
@login_required
def leave_room_route(room_id):
    chat_room = Room.query.get_or_404(room_id)
    if chat_room.members.filter_by(id=current_user.id).first():
        chat_room.members.remove(current_user)
        db.session.commit()
        flash(f'You left #{chat_room.name}.', 'info')
    return redirect(url_for('chat.rooms'))

@chat_bp.route('/private/<int:user_id>')
@login_required
def private(user_id):
    if user_id == current_user.id:
        flash('You can not chat with yourself.', 'warning')
        return redirect(url_for('chat.rooms'))
    
    other_user = db.session.get(User, user_id)
    if not other_user:
        abort(404)
        
    PrivateMessage.query.filter_by(
        sender_id=other_user.id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    messages = PrivateMessage.query.filter(
        db.or_(
            db.and_(PrivateMessage.sender_id == current_user.id,
                    PrivateMessage.receiver_id == other_user.id),
            db.and_(PrivateMessage.sender_id == other_user.id,
                    PrivateMessage.receiver_id == current_user.id)
        )
    ).order_by(PrivateMessage.timestamp.asc()).limit(50).all()
    
    friends = current_user.get_friends()
    
    return render_template(
        'chat/private.html',
        other_user=other_user,
        messages=messages,
        friends=friends,
        title=f'Chat With {other_user.username}'
    )