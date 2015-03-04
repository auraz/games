import re
import urllib
import urllib2
import json

from app import app


_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')


def get_steam_userinfo(steam_id):
    """
    Get user info dict from steam by steam id.

    Returns

    {u'steamid': u'76561198063129605', u'primaryclanid': u'103582791429521408', u'realname': u'Alexander', u'personaname': u'Experimentator', u'personastate': 0, u'personastateflags': 0, u'communityvisibilitystate': 3, u'loccountrycode': u'UA', u'profilestate': 1, u'profileurl': u'http://steamcommunity.com/profiles/76561198063129605/', u'timecreated': 1336290435, u'avatar': u'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/6e/6e4731ff785a323c8454916c48c016a31d6165b9.jpg', u'locstatecode': u'12', u'avatarfull': u'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/6e/6e4731ff785a323c8454916c48c016a31d6165b9_full.jpg', u'avatarmedium': u'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/6e/6e4731ff785a323c8454916c48c016a31d6165b9_medium.jpg', u'lastlogoff': 1425465513}
    """
    options = {
        'key': app.config['STEAM_API_KEY'],
        'steamids': steam_id
    }
    url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
    rv = json.load(urllib2.urlopen(url))
    return rv['response']['players']['player'][0] or {}
