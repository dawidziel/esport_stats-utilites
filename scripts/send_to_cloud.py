import os
import base64
import pandas as pd
import sys
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from sqlalchemy import create_engine, exc, delete
from cloud_scripts import *
from config import *
from playerLeaguepedia import PlayerLeaguepedia
from soloq.soloq import Soloq
from maps import Maps


def send_data(team_code, team_players, game_type, sheet_name=None, soloq_bool=False):
    decrypted_pg_pwd = base64.b64decode(pg_password).decode('utf-8')

    if game_type == "official_games":
        engine = create_engine(engine_str_official % decrypted_pg_pwd)
    else:
        engine = create_engine(engine_str_scrim % decrypted_pg_pwd)
    if sheet_name==None: sheet_name=team_code

    game_urns = tuple(pd.read_sql("select distinct team_stats.*, player_stats.date from team_stats inner join player_stats on \
                                  player_stats.live_data_match_urn = team_stats.live_data_match_urn where team_stats.team_name = '%s' \
                                  and date>'2023-01-01' and player_stats.league_id!='98767991335774713'" % team_code, engine)['live_data_match_urn'].unique())
    drafts = pd.read_sql("SELECT * FROM drafts WHERE live_data_match_urn IN {}".format(game_urns), engine).iloc[::-1].reset_index(drop=True)
    team_stats = pd.read_sql("SELECT distinct team_stats.*, player_stats.date FROM team_stats inner join player_stats on \
                             player_stats.live_data_match_urn = team_stats.live_data_match_urn WHERE team_stats.live_data_match_urn IN {}\
                             ".format(game_urns), engine).iloc[::-1].reset_index(drop=True)
    player_stats = pd.read_sql("SELECT * FROM player_stats WHERE live_data_match_urn IN {}".format(game_urns), engine)
    builds = pd.read_sql('select date, esports_game_id, player_stats.game_time, player_stats.patch, summoner_name, role, player_stats.result, \
        champion_name, team_stats.team_name, items.*, runes.*, champions_killed as kills, \
        num_deaths as deaths, assists, (player_stats."gold_diff@14" + "xp_diff@14") as "gxd@14", \
        gspd, team_stats."gold_diff@14" as "team_gd@14", first_herald, elemental_drakes_killed, barons_killed, player_stats.side \
        from player_stats inner join items on (player_stats.live_data_match_urn = items.live_data_match_urn AND \
        player_stats.live_data_player_urn = items.live_data_player_urn) inner join runes on\
        (items.live_data_match_urn = runes.live_data_match_urn AND \
        items.live_data_player_urn = runes.live_data_player_urn) inner join team_stats on \
        (player_stats.live_data_match_urn = team_stats.live_data_match_urn and \
        player_stats.live_data_team_urn = team_stats.live_data_team_urn) where player_stats.live_data_match_urn IN {}\
        order by date desc, player_stats.live_data_team_urn'.format(game_urns), engine)
    builds = builds.drop(columns=['live_data_match_urn', 'live_data_player_urn'])

    event_df = pd.read_sql("select event_positions.*, events.game_time, events.objective_type,events.objective_name, \
                            events.objective_nr, events.killer_team_urn, events.blue_gold_spent, events.red_gold_spent, \
                            drafts.blue_team_name, drafts.red_team_name from event_positions left join events on \
                            (event_positions.live_data_match_urn=events.live_data_match_urn and event_positions.objective_id= \
                            events.objective_id) left join drafts on event_positions.live_data_match_urn=drafts.live_data_match_urn\
                            where event_positions.live_data_match_urn IN {}".format(game_urns), engine)

    # Sorting data
    drafts = drafts.sort_values(by='date', ascending=False)
    team_stats = team_stats.sort_values(by='date', ascending=False)

    # Leaguepedia
    try:
        PL = PlayerLeaguepedia("2022-01-01", "2023-12-30")
        leaguepedia_df = PL.player_stats(team_players)
        leaguepedia_df = leaguepedia_df.replace(player_old_names)
        modify_data_worksheet(leaguepedia_df, 1, sheet_name, 'leaguepediaGames')
    except Exception as e:
        print(e)

    # SOLOQ
    if soloq_bool==True:
        if team_code in ['WOLF', 'EXD', 'KNF', 'ESCA', 'AB']:
            lolpros_code = team_code + '1'
        else:
            lolpros_code = team_code

        S = Soloq(lolpros_code)
        soloq_df, multi_opgg, multi_lolpros = S.create_soloq_df()
        modify_data_worksheet(soloq_df, 1, sheet_name, 'soloqData')
        add_hyperlink(sheet_name, 'Drafts', 'K1', multi_opgg)
        add_hyperlink(sheet_name, 'Drafts', 'P1', multi_lolpros)

    modify_data_worksheet(drafts, 1, sheet_name, 'draftData')
    modify_data_worksheet(team_stats, 1, sheet_name, 'teamData')
    modify_data_worksheet(player_stats, 1, sheet_name, 'playerData')

    Creating maps
    M = Maps()
    current_map_df = read_cloud_df(sheet_name, 'mapInfo')
    try:
        current_matches = current_map_df['live_data_match_urn'].unique()
    except:
        current_matches = []
    event_df = event_df[~event_df['live_data_match_urn'].isin(current_matches)]

    if len(event_df.index)>0:
        print("UPDATE %s gier" % str(len(event_df['live_data_match_urn'].unique())))
        maps_df = M.send_maps(event_df, game_type)
        maps_df = pd.concat([current_map_df, maps_df]).reset_index(drop=True)
        modify_data_worksheet(maps_df, 1, sheet_name, 'mapInfo')

    try:
        modify_data_worksheet(builds, 1, sheet_name, 'buildData')
    except:
        print("no build data")

for team in team_info:
    print(team)
    try:
        send_data(team, team_info[team], "official_games", soloq_bool=True)
        time.sleep(30)
    except:
        continue

for team in other_team_info:
    print(team)
    send_data(team, other_team_info[team], "official_games")
    time.sleep(30)
