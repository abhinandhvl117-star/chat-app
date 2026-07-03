from datetime import datetime, timezone
from app.extensions import db


class RoomMessage(db.Model):

    __tablename__ = 'room_messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    content = db.Column(db.Text, nullable=False)             # ← removed 'context' alias
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'username': self.author.username,
            'profile_picture': self.author.profile_picture,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%H:%M'),
            'full_timestamp': self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f'<RoomMessage room={self.room_id} user={self.user_id}>'


class PrivateMessage(db.Model):

    __tablename__ = 'private_messages'                      

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          index=True)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_username': self.sender.username,
            'sender_picture': self.sender.profile_picture,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%H:%M'),
            'full_timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
        }

    def __repr__(self):
        return f'<PrivateMessage {self.sender_id} to {self.receiver_id}>'