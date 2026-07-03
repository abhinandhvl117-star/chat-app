from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_picture = db.Column(db.String(256), default='default.png')
    bio = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_online = db.Column(db.Boolean, default=False)
    
    # relationship
    
    room_messages = db.relationship('RoomMessage', backref='author', lazy='dynamic', foreign_keys='RoomMessage.user_id')
    sent_messages = db.relationship('PrivateMessage', backref='sender', lazy='dynamic', foreign_keys='PrivateMessage.sender_id')
    received_messages = db.relationship('PrivateMessage', backref='receiver', lazy='dynamic', foreign_keys='PrivateMessage.receiver_id')
    sent_requests = db.relationship('FriendRequest', backref='sender', lazy='dynamic', foreign_keys='FriendRequest.sender_id')
    received_requests = db.relationship('FriendRequest', backref='receiver', lazy='dynamic', foreign_keys='FriendRequest.receiver_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def ping(self):
        self.last_seen = datetime.now(timezone.utc)
        db.session.add(self)
        
    def get_friends(self):
        # Returns a list of User objects who are friends with this user.
        # A Friendship row exists for each pair — we check both columns
        # because friendship is symmetric (if A-B exists, B-A doesn't need to)
        from app.models.friend import Friendship
        
        friends_as_user1 = db.session.query(User).join(
            Friendship, Friendship.user2_id == User.id
        ).filter(Friendship.user1_id == self.id).all()
        
        friends_as_user2 = db.session.query(User).join(
            Friendship, Friendship.user1_id == User.id
        ).filter(Friendship.user2_id == self.id).all()
        
        return friends_as_user1 + friends_as_user2
    
    def is_friend_with(self, user):
        # Returns True if there is a Friendship row between self and user
        from app.models.friend import Friendship
        
        return Friendship.query.filter(
            db.or_(
                db.and_(Friendship.user1_id == self.id, Friendship.user2_id == user.id),
                db.and_(Friendship.user1_id == user.id, Friendship.user2_id == self.id)
            )
        ).first() is not None
        
    def has_pending_request_to(self, user):
        # Returns True if self sent a pending friend request to user
        from app.models.friend import FriendRequest
        
        return FriendRequest.query.filter_by(
            sender_id = self.id, receiver_id=user.id, status='pending'
        ).first() is not None
        
    def get_unread_message_count(self, sender):
        # Count unread private messages from a specific sender
        from app.models.message import PrivateMessage
        return PrivateMessage.query.filter_by(
            sender_id = sender.id,
            receiver_id = self.id,
            is_read = False
        ).count()
        
    def __repr__(self):
        return f'<User {self.username}>'