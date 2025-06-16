import os
import base64
import pandas as pd
import sys
import numpy as np
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.append('/root/bayes/')
from sqlalchemy import create_engine, exc, delete
from config import *
from cloud_scripts import *

sheet_name = 'rofle do pobrania wow'
decrypted_pg_pwd = base64.b64decode(pg_password).decode('utf-8')
cloud_map_df = read_cloud_df(sheet_name, 'draftData')

engine = create_engine(engine_str_official % decrypted_pg_pwd)

summoners = ("WLG WaenA","EIQ Eren","OPL Peng","GO Ronaldo","ESCA Dawidsonek","MRS xKenzuke",
             "GSK trace","SMB Pout","ION Marrow Ooze","SMB Ksaez","ME RangJun","ANO Dom1nant",
             "OFF7 Karoq","PTA Tonerre","GS Ksaez","SNG Merza","GSMC Alvanai","ION William4",
             "GIA Jiizuke","DTG Toybu","GSNS Hydra","DTG Laynel","5R Memo","SLY Peng","SMB Camanagazo",
             "FB stillnumb","EE Lmzs","KRM Cdric","VNR ERIXEN","5R azgNeym","BFC Phoxie","ANO Lowkey",
             "DV1 Domoles","SMS coing","AUR Kunduz","SMS Kazuki","EGN Seem","SNG Piccione","FTW Dragon","LION Achilles")


# getting data
drafts = pd.read_sql("select player_stats.live_data_match_urn, league_info.name as league, player_stats.date, \
                    MAX(drafts.patch), MAX(drafts.blue_team_name), \
                    MAX(drafts.red_team_name), MAX(drafts.winner_team), MAX(drafts.b_b1), \
                    MAX(drafts.r_b1), MAX(drafts.b_b2), MAX(drafts.r_b2), MAX(drafts.b_b3), \
                    MAX(drafts.r_b3), MAX(drafts.r_b4), MAX(drafts.b_b4), MAX(drafts.r_b5), \
                    MAX(drafts.b_b5), MAX(drafts.b1), MAX(drafts.r1), MAX(drafts.r2), MAX(drafts.b2), \
                    MAX(drafts.b3), MAX(drafts.r3), MAX(drafts.r4), MAX(drafts.b4), MAX(drafts.b5), \
                    MAX(drafts.r5), MAX(drafts.b1_role), MAX(drafts.r1_role), \
                    MAX(drafts.r2_role), MAX(drafts.b2_role), MAX(drafts.b3_role), \
                    MAX(drafts.r3_role), MAX(drafts.r4_role), MAX(drafts.b4_role), \
                    MAX(drafts.b5_role), MAX(drafts.r5_role), MAX(drafts.rolf_urn), MAX(player_stats.summoner_name) \
                    from drafts left join player_stats on \
                    player_stats.live_data_match_urn = drafts.live_data_match_urn \
                    left join league_info on \
                    player_stats.league_id = league_info.id \
                    where player_stats.summoner_name in {}\
                    group by player_stats.live_data_match_urn, player_stats.date, league_info.id".format(summoners), engine)

cols = ['live_data_match_urn', 'league', 'date', 'patch', 'blue_team', 'red_team', 'winner',
        'b_b1', 'r_b1', 'b_b2', 'r_b2', 'b_b3', 'r_b3', 'r_b4', 'b_b4', 'r_b5', 'b_b5', 'b1', 'r1', 
        'r2', 'b2', 'b3', 'r3', 'r4', 'b4', 'b5', 'r5', 'b1_role', 'r1_role', 'r2_role', 'b2_role', 
        'b3_role', 'r3_role', 'r4_role', 'b4_role', 'b5_role', 'r5_role', 'rolf_urn', 'summoner_name']

roles = ['b1_role', 'r1_role', 'r2_role', 'b2_role', 'b3_role', 'r3_role', 
        'r4_role', 'b4_role', 'b5_role', 'r5_role']

drafts.columns = cols
xd_cols = ['b_Top', 'b_Jungle', 'b_Mid', 'b_Bot', 'b_Support', 'r_Top', 'r_Jungle', 'r_Mid', 'r_Bot', 'r_Support']
drafts_wtf = pd.DataFrame()

for row in drafts.to_dict(orient='records'):
    temp_row = {k: v for (k,v) in row.items() if k in roles}
    xd = {k[0]+'_'+v: row[k.split('_')[0]] for (k, v) in temp_row.items()}
    try:
        wtfs = pd.DataFrame(xd, index=[0])
        wtfs = wtfs[xd_cols]
        for col in reversed(['live_data_match_urn', 'league', 'date', 'patch', 'blue_team', 'red_team', 'winner', 'rolf_urn']):
            wtfs.insert(0, col, row[col])
        wtfs['summoner_name'] = row['summoner_name']
        drafts_wtf = pd.concat([drafts_wtf, wtfs])
    except:
        continue

drafts_wtf = drafts_wtf.sort_values(by=['date'], ascending=False).reset_index(drop=True)
drafts_wtf.to_csv("midlaners_games.csv")
