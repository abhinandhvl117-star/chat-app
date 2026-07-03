from datetime import datetime, timezone
from app.extensions import db


class FriendRequest(db.Model):

    __tablename__ = 'friend_requests'   

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                            nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('sender_id', 'receiver_id', name='unique_friend_request'),
    )

    def __repr__(self):
        return f'<FriendRequest {self.sender_id} to {self.receiver_id} [{self.status}]>'


class Friendship(db.Model):

    __tablename__ = 'friendships'       

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_friendship'),
    )

    @staticmethod
    def create(user1_id, user2_id):
        uid1, uid2 = min(user1_id, user2_id), max(user1_id, user2_id)
        friendship = Friendship(user1_id=uid1, user2_id=uid2)
        db.session.add(friendship)
        db.session.commit()
        return friendship              

    def __repr__(self):
        return f'<Friendship {self.user1_id} between {self.user2_id}>'