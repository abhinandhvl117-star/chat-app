from flask import render_template, redirect, url_for, request, jsonify,flash
from flask_login import login_required, current_user
from app.friends import friends_bp
from app.models import User, FriendRequest, Friendship
from app.extensions import db

@friends_bp.route('/')
@login_required
def index():
    friends = current_user.get_friends()
    pending_received = FriendRequest.query.filter_by(
        receiver_id = current_user.id,
        status = 'pending'
    ).all()
    
    pending_sent = FriendRequest.query.filter_by(
    sender_id=current_user.id,
    status='pending'
    ).all() 
    
    return render_template(
        'friends/index.html',
        friends=friends,
        pending_received=pending_received,
        pending_sent=pending_sent,
        title='Friends'
    )
    
@friends_bp.route('/search')
@login_required
def search():
    query = request.args.get('q','').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
    User.username.ilike(f'%{query}%'),         
    User.id != current_user.id
    ).limit(10).all()
    
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'username': user.username,
            'profile_picture': user.profile_picture,
            'is_friend': current_user.is_friend_with(user),
            'request_sent': current_user.has_pending_request_to(user),
            'profile_url': url_for('profile.view', username=user.username)
        })
        
    return jsonify(results)

@friends_bp.route('/request/<int:user_id>', methods=['POST'])
@login_required
def send_request(user_id):
    # prevent sending self request
    if user_id == current_user.id:
        flash('you cannot send a friend request to yourself.', 'warning')
        return redirect(url_for('friends.index'))
    
    target_user = db.session.get(User, user_id)
    if not target_user:
        flash('User not found', 'danger')
        return redirect(url_for('friends.index'))
    
    # prevent sending duplicate request
    if current_user.has_pending_request_to(target_user):
        flash('Friend request already sent.', 'info')
        return redirect(url_for('profile.view', username=target_user.username))
    
    # prevent sending request to friend
    if current_user.is_friend_with(target_user):
        flash('You are already friends.', 'info')
        return redirect(url_for('profile.view', username=target_user.username))
    
    # Check if the other user already sent US a request
    existing = FriendRequest.query.filter_by(
        sender_id=target_user.id,
        receiver_id=current_user.id,
        status='pending',
    ).first()
    
    if existing:
        # auto accept
        existing.status = 'accepted'
        Friendship.create(current_user.id, target_user.id)
        db.session.commit()
        flash(f'You are now friends with {target_user.username}.', 'success')
        return redirect(url_for('profile.view', username=target_user.username))
    
    # create new friend request
    friend_request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        status='pending'
    )
    db.session.add(friend_request)
    db.session.commit()
    
    flash(f'Friend request sent to {target_user.username}.', 'success')
    return redirect(url_for('profile.view', username=target_user.username))

@friends_bp.route('/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # Security: only the receiver can accept the request.
    if friend_request.receiver_id != current_user.id:
        flash('You are not authorized to accept this request.', 'danger')
        return redirect(url_for('friends.index'))
    
    if friend_request.status != 'pending':
        flash('This request has already been handled.', 'info')
        return redirect(url_for('friends.index'))
    
    friend_request.status = 'accepted'
    
    Friendship.create(friend_request.sender_id, friend_request.receiver_id)
    db.session.commit()
    
    sender = db.session.get(User, friend_request.sender_id)
    flash(f'You are now friends with {sender.username}.', 'success')
    return redirect(url_for('friends.index'))

@friends_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # Security: only the receiver can reject.
    if friend_request.receiver_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('friends.index'))
    
    friend_request.status = 'rejected'
    db.session.commit()
    
    flash('Friend request declined.', 'info')
    return redirect(url_for('friends.index'))

@friends_bp.route('/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    target_user = db.session.get(User, user_id)
    if not target_user:
        flash('User not found.', 'danger')
        return redirect(url_for('friends.index'))
    
    friendship = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.user1_id == current_user.id,
                    Friendship.user2_id == target_user.id),
            db.and_(Friendship.user1_id == target_user.id,
                    Friendship.user2_id == current_user.id)
        )
    ).first()
    
    if friendship:
        db.session.delete(friendship)
        
        FriendRequest.query.filter(
            db.or_(
                db.and_(FriendRequest.sender_id == current_user.id,
                        FriendRequest.receiver_id == target_user.id),
                db.and_(FriendRequest.sender_id == target_user.id,
                        FriendRequest.receiver_id == current_user.id)
            )
        ).delete()
        
        db.session.commit()
        flash(f'{target_user.username} has been removed from your friends.', 'info')
    
    else:
        flash('Friendship not found.', 'warning')
        
    return redirect(url_for('friends.index'))