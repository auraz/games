import datetime
from hashlib import md5

from flask.ext.login import UserMixin

from app import db


class UserSocial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    facebook_id = db.Column(db.String(64))
    steam_id = db.Column(db.String(40))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(120))
    teams_and_games = db.relationship('TeamGameUserRelation', backref='player', lazy='dynamic')
    user_social = db.relationship('UserSocial', uselist=False, backref="user")

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


    @staticmethod
    def get_or_create(property, social_id, **kwargs):
        """
        property is steam_id or facebook_id
        """

        property = property + '_id'
        if property == 'facebook_id':
            rv = UserSocial.query.filter_by(facebook_id=social_id).all()
        else:
            rv = UserSocial.query.filter_by(steam_id=social_id).all()

        if len(rv) > 1:
            rv = User.merge(rv) # finish merge, how?
        elif len(rv) == 1:
            rv = rv[0]
        else:  # rv is None
            linked_rv = User.try_link(property, social_id)

            if linked_rv:
                return linked_rv

            nickname, email = kwargs.get('nickname'), kwargs.get('email')
            rv = User(nickname=nickname, email=email)
            user_social = UserSocial(user=rv)
            setattr(user_social, property, social_id)
            db.session.add(rv)
            db.session.commit()

        return rv

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    @classmethod
    def try_link(cls, property, social_id):
        """
        # check fo r cookie, if cookie exists, link
            # http://stackoverflow.com/questions/6666267/architecture-for-merging-multiple-user-accounts-together

            # check if emails are same.
            # is so link!
        """
        # import ipdb; ipdb.set_trace()
        pass

    @classmethod
    def merge(cls, rv):
        """
        Merge users from queryset
        """
        chosen_user = rv.first()
        import ipdb; ipdb.set_trace()

        # choose nickname, email and about me, and last_seen

        # update other user_ids of TeamGameUserRelation and GameRequest

        return chosen_user

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
