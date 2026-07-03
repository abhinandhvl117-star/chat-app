from flask import Blueprint

friends_bp = Blueprint('friends', __name__)

from app.friends import routes