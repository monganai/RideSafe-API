from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# # user model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return ' < User {} > '.format(self.username)

# # crash location points 
class CrashLocationPoint(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    latitude = db.Column(db.String(140))
    longitude = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return ' < CrashLocationPoint {} > '.format(self.body)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# # crash point values
class CrashDataPoint(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    gforce = db.Column(db.String(140))
    rotation = db.Column(db.String(140))
    classification = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)

    def __repr__(self):
        return ' < CrashLocationPoint {} > '.format(self.body)
