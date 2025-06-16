import pandas as pd
import urllib.request
import json
import mwclient
import requests


site = mwclient.Site('lol.fandom.com', path='/')
response = site.api('cargoquery',
    limit = "max",
    tables = "Leagues=L",
    fields = "L.League",
    where = 'L.Region =  "Europe" and L.IsOfficial = "Yes"'
)
leagues_response = json.dumps(response)
leagues = [x['title']['League'] for x in json.loads(leagues_response)['cargoquery']]

players = []
for league in leagues:
    site = mwclient.Site('lol.fandom.com', path='/')
    response = site.api('cargoquery',
        limit = "max",
        tables = "PlayerLeagueHistory=PH",
        fields = "PH.Player, PH.League",
        where = 'PH.League =  "%s"' % league
    )
    players_response = json.dumps(response)
    players.extend([x['title']['Player'] for x in json.loads(players_response)['cargoquery']])

df = pd.DataFrame()
for player in players:
    if player in df.values :
        continue

    site = mwclient.Site('lol.fandom.com', path='/')
    response = site.api('cargoquery',
        limit = "max",
        tables = "Players=P",
        fields = "P.ID, P.Player, P.Name, P.Role, P.Team, P.Residency, P.Lolpros, P.IsSubstitute",
        where = 'P.Player =  "%s" and P.IsRetired = "No"' % player
    )
    player_info_response = json.dumps(response)
    player_info = json.loads(player_info_response)
    df_player = pd.json_normalize(player_info['cargoquery'])
    df = df.append(df_player)

df.to_csv("bayes/data/player_roles.csv")
