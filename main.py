from sqlalchemy import create_engine, exc, delete
import os
from get_token import get_token
from getgames import GetGames
import pandas as pd
from cloud_scripts import *
import time
import base64
import numpy as np
from config import *
import sys


start = time.time()
try:
    mode = sys.argv[1]
except:
    mode = 'OFFICIAL'
fail_date = '2023-01-01T11:59:59Z'      # starting date if db does not exist
abs_path = os.path.dirname(os.path.abspath(__file__))
decrypted_pg_pwd = base64.b64decode(pg_password).decode('utf-8')
token = get_token()
G = GetGames(abs_path, token)


# initializing functions according to provided arg
if mode == 'OFFICIAL':
    engine = create_engine(engine_str_official % decrypted_pg_pwd)
    last_game, old_game_ids, old_match_urns = G.get_old_ids(engine, fail_date)
    id_error_list = G.get_error_ids(engine)
    old_game_ids = np.concatenate((old_game_ids, id_error_list))

    last_game = '2023-01-01T11:59:59Z'
    league_df = pd.read_sql("select * from league_info", engine)
    league_ids = league_df[league_df['name'].isin(league_names)]['id'].unique()
    ids = G.get_official_id(last_game, league_ids, old_game_ids)

    print("Script will download stats for: %s games" % str(len(ids)))
    G.download_from_ids(ids, 'OFFICIAL', engine, league_df, old_match_urns)
elif mode == 'SCRIM':
    engine = create_engine(engine_str_scrim % decrypted_pg_pwd)
    last_game, old_game_ids, old_match_urns = G.get_old_ids(engine, fail_date)
    id_error_list = G.get_error_ids(engine)
    old_game_ids = np.concatenate((old_game_ids, id_error_list))
    last_game = '2023-01-01T11:59:59Z'
    ids = G.get_scrim_ids(last_game, old_game_ids)

    print("Script will download stats for: %s games" % str(len(ids)))
    G.download_from_ids(ids, 'SCRIM', engine, None, old_match_urns)
elif mode == 'EMH':
    print("not yet done")
elif mode == 'FAILURE_RERUN':
    engine_official = create_engine(engine_str_official % decrypted_pg_pwd)
    engine_scrim = create_engine(engine_str_scrim % decrypted_pg_pwd)

    # get error ids from dbs
    id_official = G.get_error_ids(engine_official)
    id_official = [x for x in id_official if int(x) > 108999999999999999]
    id_official = []

    id_scrim = G.get_error_ids(engine_scrim)
    league_df = pd.read_sql("select * from league_info", engine_official)

    print("Script will download stats for: %s games" % str(len(id_official)))
    G.download_from_ids(id_official, 'OFFICIAL', engine_official, league_df)

    print("Script will download stats for: %s games" % str(len(id_scrim)))
    G.download_from_ids(id_scrim, 'SCRIM', engine_scrim)

    engine_scrim.dispose()
    engine_official.dispose()

if mode != 'FAILURE_RERUN':
    engine.dispose()

end = time.time()
print(end - start)
