from datetime import datetime, timezone
from app.extensions import db

room_members = db.Table(
    'room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
)

class Room(db.Model):
    
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) 
    
    members = db.relationship('User', secondary=room_members, backref=db.backref('rooms', lazy='dynamic'), lazy='dynamic')
    messages = db.relationship('RoomMessage', backref='rooms', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def member_count(self):
        return self.members.count()
    
    def __repr__(self):
        return f'<Room {self.name}>'