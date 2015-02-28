import datetime
import sqlalchemy

from flask import render_template, flash, redirect, session, url_for, request, g, send_from_directory
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask import Flask, render_template, request, make_response

from app import app, db, lm, oid
from forms import LoginForm, EditForm, RequestGameForm
from models import User, UserSocial, Game, GameRequest, Team, TeamGameUserRelation
from match import calculate_matches
from oauth import OAuthSignIn
from steam_openid import get_steam_userinfo, _steam_id_re
from merge_accounts import merge_accounts


@app.route('/authorize/<provider>')
@oid.loginhandler
def oauth_authorize(provider):
    """
    Authorize callback for oauth provider.
    """
    if not current_user.is_anonymous():
        is_facebook = current_user.user_social.facebook_id
        is_steam = current_user.user_social.steam_id
        if is_steam and is_facebook:
            return redirect(url_for('index'))
        # this means that we want to link accounts, procceed
    if provider == 'facebook':
        oauth = OAuthSignIn.get_provider(provider)
        return oauth.authorize()
    else:  # steam
        return oid.try_login('http://steamcommunity.com/openid')


@app.route('/callback/<provider>')
def oauth_callback(provider):
    """
    Oauth callback.
    """
    oauth = OAuthSignIn.get_provider(provider)
    social_id, nickname, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    if not current_user.is_anonymous():
        user_id = current_user.id
        merge_accounts('steam_id', 'facebook_id', social_id, nickname, user_id,email)
        return redirect(url_for('index'))
    user = User.get_or_create(provider, social_id, nickname=nickname, email=email)
    login_user(user, True)
    return redirect(url_for('index'))


@oid.after_login
def after_login(resp):
    """
    Callback for openid logins
    """
    match = _steam_id_re.search(resp.identity_url)
    steam_id =  match.group(1)
    if steam_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    steamdata = get_steam_userinfo(steam_id)
    nickname = steamdata['personaname']
    if not current_user.is_anonymous():
        # get user id, as current user is not passable to another function
        # if code of merge is here, it works, why?
        user_id = current_user.id
        merge_accounts('facebook_id', 'steam_id', steam_id, nickname, user_id)
        return redirect(url_for('index'))
    user = User.get_or_create('steam', steam_id, nickname=nickname)
    if user is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    login_user(user, True)  # i think login_user will store user in flask.session
    return redirect(url_for('index'))

@app.route('/')
def login():
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/index')
def index():
    if current_user.is_anonymous():
        return redirect(url_for('login'))
    user = g.user
    games = [
        {
            'name': 'Dota 2'
        },
        {
            'name': 'AoW'
        }
    ]
    teams = [
        {
            'name': 'Yahoo'
        },
        {
            'name': 'Strategists'
        }
    ]
    assosiations = [
        {
            'player': {'nickname': 'John'},
            'game': {'name': 'Dota 2'},
            'team': {'name': 'Yahoo'}
        },
        {
            'player': {'nickname': 'John'},
            'game': {'name': 'AoW 3'},
            'team': {'name': 'Strategists'}
        },
    ]

    requested_games=GameRequest.query.filter_by(user_id=g.user.id).all()
    # games = [
    #     (Game.query.filter_by(id=game.game_id).first().name,
    #     game.schedule_datetime,
    #     game.game_interval) for game in requested_games]
    games = [(
    Game.query.filter_by(id=game.game_id).first().name,
    game.schedule_datetime,
    game.game_interval,
    calculate_matches(game)
    ) for game in requested_games]
    return render_template(
        "index.html",
        title='Home',
        user=user,
        games=games,
        teams=teams,
        assosiations=assosiations,
        requested_games=games
    )


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/<nickname>')  # why /abc/<nickname> adds prefix for static /abc/static
@login_required
def nickname(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))

    games = [
        {
            'name': 'Dota 2'
        },
        {
            'name': 'AoW'
        }
    ]
    teams = [
        {
            'name': 'Yahoo'
        },
        {
            'name': 'Strategists'
        }
    ]
    return render_template(
        "user.html",
        user=user,
        games=games,
        teams=teams,
    )


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.route('/request_game', methods=['GET', 'POST'])
@login_required
def request_game():
    form = RequestGameForm()
    form.game_id.choices = [(game.id, game.name) for game in Game.query.order_by('name')]
    if not form.game_id.choices:
        g1 = Game(name='Dota 2')
        g2 = Game(name='AoW')
        db.session.add(g1)
        db.session.add(g2)
        db.session.commit()
        form.game_id.choices = [(game.id, game.name) for game in Game.query.order_by('name').all()]
    if form.validate_on_submit():
        gr = GameRequest(
            user_id=g.user.id,
            game_id=form.game_id.data,
            schedule_datetime=form.schedule_datetime.data,
            game_interval=datetime.timedelta(minutes=form.interval.data)
        )
        other_requests = GameRequest.query.join(User).join(Game).filter(
            sqlalchemy.and_(
                Game.id==gr.game_id,
                User.id == gr.user_id
            )
        ).all()
        if any([gr.schedule_datetime.date() == req.schedule_datetime.date() for req in other_requests]):
            flash('You already have request for this game for this date. Try to change date.')
            return redirect(url_for('request_game'))
        try:
            db.session.add(gr)
            db.session.commit()
            flash('Your request have been saved.')
            return redirect(url_for('request_game'))
        except sqlalchemy.exc.IntegrityError as err:
            flash('Same request exists, try to change values.')
            return redirect(url_for('request_game'))
    else:
        requested_games=GameRequest.query.filter_by(user_id=g.user.id).all()
        games = [(
            Game.query.filter_by(id=game.game_id).first().name,
            game.schedule_datetime,
            game.game_interval,
            calculate_matches(game)
        ) for game in requested_games]
        return render_template('request_game.html', form=form, requested_games=games)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/games', methods=['GET'])
def list_of_games():
    return render_template('games.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')

