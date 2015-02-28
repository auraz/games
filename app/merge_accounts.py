from app import db
from models import User, UserSocial, Game, GameRequest, Team, TeamGameUserRelation



def merge_accounts(logged_account, linked_account, social_id, linked_nickname, current_user_id, linked_email=None):
    """
    Merge linked_accout to logged_account

    logged_account: account user logged in
    linked_accout: user just press link and we are in callback from provider.
    """
    current_user = User.query.filter_by(id=current_user_id).first()
    assert current_user.user_social.__dict__.get(logged_account)

    # we already my have this user in database, with steam account
    # so we need to merge information and delete account

    # check if user already logged with steam
    query_kwargs = {linked_account: social_id}
    existing_user_social = UserSocial.query.filter_by(**query_kwargs).first()
    if existing_user_social: # if we have it, do merge
        assert not existing_user_social.__dict__.get(logged_account)
        existing_user = existing_user_social.user

        if existing_user.nickname:
            if current_user.nickname:
                current_user.nickname += ' ' + existing_user.nickname
            else:
                current_user.nickname = existing_user.nickname

        if existing_user.about_me:
            if current_user.about_me:
                current_user.about_me += ' ' + existing_user.about_me
            else:
                current_user.about_me = existing_user.about_me

        if not current_user.email:
            if existing_user.email:
                email = existing_user.email
                existing_user.email = ''  # to avoid integrity error, as email unique
                current_user.email = email

        # update teams_and_games, and games requests

        GRs = GameRequest.query.filter_by(user_id=existing_user.id).all()
        TGURs = TeamGameUserRelation.query.filter_by(user_id=existing_user.id).all()
        for gr in GRs:
            gr.user_id = current_user.id
            db.sessin.add(gr)
        for tgur in TGURs:
            tgur.user_id = current_user.id
            db.session.add(tgur)

        # delete existing_user and existing_user_social
        db.session.delete(existing_user)
        db.session.delete(existing_user_social)
        db.session.commit()

    else:
        if linked_nickname:
            if current_user.nickname:
                current_user += ' ' + linked_nickname
            else:
                current_user = linked_nickname

        if linked_email:
            if not current_user.email:
                current_user.emal = linked_email

    setattr(current_user.user_social, linked_account, social_id)
    db.session.add(current_user)
    db.session.commit()
