import datetime
from hashlib import md5

from flask.ext.login import UserMixin

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    teams_and_games = db.relationship('TeamGameUserRelation', backref='player', lazy='dynamic')

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (
            md5(self.email.encode('utf-8')).hexdigest(),
            size
        )

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    number_of_players = db.Column(db.Integer)
    teams_and_users = db.relationship('TeamGameUserRelation', backref='game', lazy='dynamic')

    def __repr__(self):
        return '<Game %r>' % (self.name)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    capacity =  db.Column(db.Integer)
    name = db.Column(db.String(64))
    user_and_games = db.relationship('TeamGameUserRelation', backref='team', lazy='dynamic')

    def __repr__(self):
        return '<Team %r>' % (self.name)

class TeamGameUserRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))


class GameRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    # number_of_players = db.Column(db.Integer)
    schedule_datetime = db.Column(db.DateTime)
    game_interval = db.Column(db.Interval())
    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'game_id',
            'schedule_datetime',
            'game_interval',
            name='_unique_game_request'
        ),
    )

    def __repr__(self):
        return 'at %s within %s' % (self.schedule_datetime, self.game_interval)
