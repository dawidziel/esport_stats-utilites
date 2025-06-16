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

decrypted_pg_pwd = base64.b64decode(pg_password).decode('utf-8')
engine = create_engine(engine_str_official % decrypted_pg_pwd)

last_game = '2023-01-01T11:59:59Z'
mid_stats = pd.read_sql("select * from player_stats", engine)
print(mid_stats.columns)
games = mid_stats['live_data_match_urn'].unique()
print(games)
print(len(games))

roles = ['Top', 'Mid', 'Bot']
x=0
matchup_stats = pd.DataFrame()
for game in games:
    temp_game_data = mid_stats[mid_stats['live_data_match_urn'] == game].filter(['champion_name', 'role', 'gold_diff@8', 'cs_diff@8', 'xp_diff@8', 'kills_assists@8', 'gold_diff@14',
                                                                            'cs_diff@14', 'xp_diff@14', 'kills_assists@14', 'jungle_prox', 'jungle_prox_diff'])

    for role in roles:
        temp_game_role = temp_game_data[(temp_game_data['role'] == role)]
        if len(temp_game_role.index) < 2:
            x+=1
            continue
    
        champion_1 = temp_game_role.iloc[[0]]
        champion_1.insert(1, 'enemy_champion', temp_game_role['champion_name'].iloc[1])
        champion_2 = temp_game_role.iloc[[1]]
        champion_2.insert(1, 'enemy_champion', temp_game_role['champion_name'].iloc[0])
        matchup_stats = pd.concat([matchup_stats, champion_1, champion_2])

print(matchup_stats)
matchup_stats.to_csv('matchup_stats.csv', index=False)