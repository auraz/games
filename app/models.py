"""
For merging user models initially use http://stackoverflow.com/questions/6666267/architecture-for-merging-multiple-user-accounts-together
"""
import datetime
from hashlib import md5

from flask.ext.login import UserMixin

from app import db


class UserSocial(db.Model):
    """
    Model for social accounts.

    It is linked with usual User model by FK.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    facebook_id = db.Column(db.String(64), unique=True)
    steam_id = db.Column(db.String(40), unique=True)


class User(UserMixin, db.Model):
    """
    User information, w/o social ids.

    Social Ids are stored in UserSocial table.
    """
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    about_me = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime)
    email = db.Column(db.String(120), index=True, unique=True)
    #password = db.Column(db.String(120))  # why we need password?
    teams_and_games = db.relationship(
        'TeamGameUserRelation',
        backref='player',
        lazy='dynamic'
    )
    user_social = db.relationship('UserSocial', uselist=False, backref="user")

    def avatar(self, size):
        if self.email:
            return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (
                md5(self.email.encode('utf-8')).hexdigest(),
                size
            )
        else:
            #  details['player']['avatarmedium']
            pass

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
    def get_or_create(social_type, social_id, **kwargs):
        """
        property is steam_id or facebook_id

        Facebook provides username and email, email may be facebook, not active user email
        Steam provides steam username and no email.

        1. We will use facebook email by default
        2. We will show facebook and steam nickname on user profile and retrieve it at that time
        3. We will have our system nickname, which can be any of that nicknames
        """

        # get user social model
        social_type = social_type + '_id'
        if social_type == 'facebook_id':
            user_social = UserSocial.query.filter_by(facebook_id=social_id).all()
        else:
            user_social = UserSocial.query.filter_by(steam_id=social_id).all()

        assert len(user_social) < 2 # Only one User Social account for given social_id

        if len(user_social) == 1:  # return existing user
            return user_social[0].user

        linked_rv = User.try_link(social_type, social_id)

        # merge users if emails are equal
        if kwargs.get('email'):  # check if we have user account with same email
            # if so - merge accounts:
            # it looks like user previously logged in with steam and set email
            # and now logs with facebook
            user = User.query.filter_by(email=kwargs.get('email')).first()
            if user:
                setattr(user.user_social, social_type, social_id)
            return user

        # create new user
        nickname, email = kwargs.get('nickname'), kwargs.get('email')
        user = User(nickname=nickname, email=email)
        user_social = UserSocial(user=user)
        setattr(user_social, social_type, social_id)
        db.session.add(user)
        db.session.commit()

        return user

    def __repr__(self):
        return '<User %r>' % (self.nickname)


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
