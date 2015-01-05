from functools import partial

from sqlalchemy import and_

from models import Game, GameRequest, Team, User


def by_time(gr1, gr2):
    """
    a, b - times of starts, x,y - intervals.
    They can play if min(b+y, a+x) - max(a,b) >= min(x y)
    gr - GameRequest object
    """
    return min(
        gr1.schedule_datetime + gr1.game_interval,
        gr2.schedule_datetime + gr2.game_interval
    ) - max(
        gr1.schedule_datetime,
        gr2.schedule_datetime
    ) >= min(
        gr1.game_interval,
        gr2.game_interval
    )


def calculate_matches(game_request):
    """
    Calculate mathed GameRequests. Return first found match. (TODO: most old?)
    """
    other_requests = GameRequest.query.join(User).join(Game).filter(
        and_(
            Game.id==game_request.game_id,
            id != game_request.id,
            User.id != game_request.user_id
        )
    ).all()
    resulted_requests = filter(partial(by_time, game_request),  other_requests)
    return resulted_requests[0] if resulted_requests else None
