import numpy as np
import pandas as pd
import json
import urllib.request
import mwclient
import base64
import sys, os


sys.path.append('/root/bayes/')
from config import *
from sqlalchemy import create_engine, exc, delete


def del_team_tag(player_name):
    if len(player_name.split(" ", 1)) == 1:
        return str(player_name)
    else:
        return str(player_name.split(" ", 1)[1])


def new_player_name_to_role(player_name):
    site = mwclient.Site('lol.fandom.com', path='/')
    response = site.api('cargoquery',
                        limit="max",
                        tables="Players=P",
                        fields="P.ID, P.Player, P.Name, P.Role, P.Team, P.Residency, P.Lolpros",
                        where='P.ID =  "%s" and P.Role = "%s"' % (player_name, 'Mid')
                        )
    player_info_response = json.dumps(response)
    player_info = json.loads(player_info_response)

    try:
        player_info = player_info['cargoquery'][0]
    except:
        player_info = {}
    try:
        player_info_df = pd.DataFrame(player_info['title'], index=[0])
        player_info_df.columns = player_info_df.columns.str.lower()

        return player_info_df
    except:
        return pd.DataFrame()


decrypted_pg_pwd = base64.b64decode(pg_password).decode('utf-8')
engine = create_engine(engine_str_official % decrypted_pg_pwd)

last_game = '2023-01-01T11:59:59Z'
mid_stats = pd.read_sql("select player_stats.*, league_info.name as league_name from player_stats \
                        inner join league_info on player_stats.league_id=league_info.id where role = 'Mid'", engine)

mid_stats['player_name'] = None
mid_stats['has_team'] = True

mid_stats = mid_stats[mid_stats['league_name'].isin(league_names)]
mid_players = mid_stats['summoner_name'].unique()

for mid in mid_players:
    print(mid)
    name = del_team_tag(mid)
    temp_player = new_player_name_to_role(name)

    if temp_player.empty == False:
        if pd.isna(temp_player['team'].iloc[0]) == True:
            mid_stats.loc[mid_stats['summoner_name'] == mid, 'has_team'] = False
        mid_stats.loc[mid_stats['summoner_name'] == mid, 'player_name'] = name

    print(temp_player)

print(mid_stats)
mid_stats.to_csv('mid_stats.csv')

