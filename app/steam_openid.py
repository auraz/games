import re
import urllib
import urllib2
import json

from app import app


_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')


def get_steam_userinfo(steam_id):
    """
    Get user info dict from steam by steam id.
    """
    options = {
        'key': app.config['STEAM_API_KEY'],
        'steamids': steam_id
    }
    url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
    rv = json.load(urllib2.urlopen(url))
    return rv['response']['players']['player'][0] or {}
