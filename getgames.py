import json
import requests
import os
import wget
import pandas as pd
import re
import numpy as np
import asyncio
import functools
import concurrent.futures
import boto3


from sqlalchemy import exc
from psycopg2.extensions import register_adapter, AsIs
from zipfile import ZipFile
from config import *
from playerstats import PlayerStats
from teamstats import TeamStats
from draft import DraftData
from playerbuilds import PlayerBuilds


class GetGames:
    def __init__(self, abs_path, token) -> None:
        self.abs_path = abs_path
        self.token = token
        self.bucket = 'game.data'
        register_adapter(np.int64, AsIs)

    def format_columns_to_sql(self, df):
        return [re.sub('(?<!^)(?=[A-Z])', '_', c).lower() for c in df.columns]

    def get_old_ids(self, engine, fail_date):
        try:
            old_player_df = pd.read_sql(
                "Select live_data_match_urn, esports_game_id, date \
                from player_stats order by date desc", engine)
            last_game = old_player_df.iloc[0]['date']
            old_game_ids = old_player_df['esports_game_id'].unique()
            old_match_urns = old_player_df['live_data_match_urn'].unique()
        except:
            last_game = fail_date
            old_game_ids = []
            old_match_urns = []

        return last_game, old_game_ids, old_match_urns

    def get_error_ids(self, engine):
        try:
            id_error_list = pd.read_sql("Select match_id from games_with_error",
                                        engine)['match_id'].unique()
        except:
            id_error_list = []

        return id_error_list
    
    def get_scrim_rofl_link(self, id):
        response = requests.get(
        'https://lolesports-api.bayesesports.com/scrim/v1/games/%s/downloadRiotReplay' % str(id),
        headers={"Authorization": f"Bearer {self.token}"})

        return response.json()['url']

    def get_official_rofl_link(self, game_id):
        game_id = game_id.upper().split(':')[-1].replace("-", "_")
        response = requests.get(
            'https://lolesports-api.bayesesports.com/emh/v1/games/%s/download' % game_id,
            headers={"Authorization": f"Bearer {self.token}"},
            params={"type": "ROFL_REPLAY"}
        )

        return response.json()['url']

    def list_leagues(self):
        response = requests.get(
            'https://lolesports-api.bayesesports.com/historic/v1/riot-lol/leagues',
            headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code != 200:
            response.raise_for_status()

        return pd.json_normalize(response.json())

    def get_scrim_ids(self, last_scrim, old_game_ids):
        page_nr = 0
        page_size = 100
        ids = []

        while page_size == 100:
            response = requests.get(
                'https://lolesports-api.bayesesports.com/scrim/v1/games',
                headers={"Authorization": f"Bearer {self.token}"},
                params={"from": last_scrim, "size": 100, 'page': page_nr}
            )
            if response.status_code != 200:
                response.raise_for_status()
            page_size = len(response.json()['games'])

            for match in response.json()['games']:
                if match['status'] != "STREAMING" and match['id'] not in old_game_ids:
                    ids.append(match['id'])
            page_nr += 1
        ids.reverse()

        return ids

    def get_official_id(self, last_game, league_ids, old_game_ids):
        page_size = 100
        page_nr = 0
        ids = []

        while page_size == 100:
            response = requests.get(
                'https://lolesports-api.bayesesports.com/historic/v1/riot-lol/matches',
                headers={"Authorization": f"Bearer {self.token}"},
                params={"leagueIds": league_ids, 'matchDateFrom': last_game, 'size': 100, 'page': page_nr})
            if response.status_code != 200:
                response.raise_for_status()

            for match in response.json()['results']:
                game_ids = []
                for game in match['match']['games']:
                    if game['downloadAvailable'] == True and game['id'] not in old_game_ids and game['id'] not in ids:
                        game_ids.append(game['id'])
                ids.extend(reversed(game_ids))
            page_size = len(response.json()['results'])
            page_nr += 1
        ids.reverse()

        return ids
    
    def upload_rofl(self, rofl_link, game_id, s3_folder):
        storage_url = '2ff7e48801fe49478de5865b7ea7f7a2'
        s3 = boto3.resource(
            service_name='s3',
            endpoint_url='https://eu2.contabostorage.com',
            aws_access_key_id='fb24c68865874faab026e71b6bbb2829',
            aws_secret_access_key='483b03a1d2bd6c7d5ed49098f444340b'
        )
        executor = concurrent.futures.ThreadPoolExecutor()
        def aio(f):
            async def aio_wrapper(**kwargs):
                f_bound = functools.partial(f, **kwargs)
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(executor, f_bound)
            return aio_wrapper
        
        r = requests.get(rofl_link, stream=True)        
        keyname = (s3_folder + (game_id.split(':')[-1]).upper() + '/' + 
                   (game_id.split(':')[-1]).upper() + '_replay.rofl')
        aio(s3.Bucket(self.bucket).upload_fileobj(r.raw, keyname))

        # returns link to s3 file
        return "https://eu2.contabostorage.com/{0}:{1}/{2}".format(storage_url, self.bucket, keyname)
        
    def download_from_ids(self, ids, game_type, engine, league_df=None, old_match_urns=[]):
        for id in ids:
            games_with_error = pd.DataFrame({'summoner_name': [None], 'match_id': [None]}, index=[0])

            if game_type == "SCRIM":
                game = requests.get(
                    'https://lolesports-api.bayesesports.com/scrim/v1/games/' +
                    str(id)+'/downloadDump',
                    headers={"Authorization": f"Bearer {self.token}"})
            elif game_type == "OFFICIAL":
                game = requests.get(
                    'https://lolesports-api.bayesesports.com/historic/v1/riot-lol/games/' +
                    str(id)+'/downloadDump',
                    headers={"Authorization": f"Bearer {self.token}"})

            try:
                wget.download(game.json()['url'], self.abs_path+"/temp/game.zip")
            except:
                continue

            # downloads zip into json into df
            with ZipFile(self.abs_path+'/temp/game.zip', 'r') as zipObj:
                zipObj.extractall(self.abs_path+"/temp")

            os.remove(self.abs_path+"/temp/game.zip")
            data = json.load(open(self.abs_path+"/temp/dump.json", "r"))

            # importing data to df, and changing column names
            temp_df = pd.json_normalize(data['events'])
            temp_df = temp_df.drop(columns=['payload.type', 'payload.version'])
            temp_df.columns = [re.sub('payload.', '', c) for c in temp_df.columns]

            # checks if game lasted longer than 15 minutes, and then runs script
            P = PlayerStats(temp_df, engine, id)
            game_id = P.game_id()

            if P.game_time() > 15 and game_id not in old_match_urns:
                try:
                    old_error_df = pd.read_sql("Select * from games_with_error", engine)
                    old_error_list = old_error_df['match_id'].tolist()
                except:
                    old_error_df = pd.DataFrame()
                    old_error_list = []

                # Gets player stats df
                try:
                    player_stats, proximity_timeline, event_positions, wards, events = P.end_game_stats()

                    if id in old_error_list:
                        games_with_error = old_error_df[old_error_df['match_id'] != id]
                        games_with_error.to_sql('games_with_error', engine,
                                                index=False, if_exists='replace')
                        print("Deleted %s from error table" % str(id))
                except:
                    #if id not in old_error_list:
                    faulty_players, faulty_roles = P.end_game_stats()
                    faulty_players.insert(0, 'match_id', id)
                    games_with_error = pd.concat([games_with_error, faulty_players]).iloc[1:]
                    games_with_error.to_sql('games_with_error', engine,
                                            index=False, if_exists='append')
                    faulty_roles_transposed = pd.merge(faulty_roles.filter(['role']).T.reset_index(drop=True),
                                                       faulty_roles.filter(['summonerName']).T.reset_index(drop=True),
                                                       left_index=True, right_index=True)
                    faulty_roles_transposed.insert(0,'id',id)
                    faulty_roles_transposed.to_csv(self.abs_path+"/data/faulty_roles_%s.csv" % game_type.lower(),
                                                   header=False, mode='a', index=False)

                    continue
                
                # Player builds
                B = PlayerBuilds(temp_df, player_stats)
                items = B.get_items()
                runes = B.get_runes()

                # Gets team stats df
                try:
                    T = TeamStats(temp_df, player_stats)
                    team_stats = T.end_game_stats()
                except:
                    continue

                # Gets Drafts df
                D = DraftData(temp_df, team_stats, player_stats, engine)
                try:
                    draft_stats = D.get_draft()
                except Exception as e:
                    print(e)
                    continue

                for df in [player_stats, team_stats, draft_stats, proximity_timeline, event_positions, wards, events]:
                    df.columns = self.format_columns_to_sql(df)

                if game_type == 'OFFICIAL':
                    # upload rofl to s3
                    try:
                        rofl_link = self.get_official_rofl_link(game_id)
                        draft_stats['rolf_urn'] = self.upload_rofl(rofl_link, game_id, 'official_games/')
                    except:
                        rofl_link = None
                    
                    # checking if league is checked for storing timelines
                    league_id = player_stats['league_id'].iloc[0]
                    if any(league_df[league_df['id'] == league_id]['timeline_bool']):
                        try:
                            # upload proximity timelite to df
                            proximity_timeline.to_sql('proximity_timeline', engine,
                                                      index=False, if_exists='append')

                        except exc.SQLAlchemyError as e:
                            error_df = pd.DataFrame({'error_id': id,
                                                     'sql_error': str(type(e))}, index=[0])
                            print(e)
                            error_df.to_csv(self.abs_path+"/data/sql_errors.csv",
                                            header=False, mode='a')
                            continue
                else:
                    # upload rofl to s3
                    try:
                        rofl_link = self.get_scrim_rofl_link(id)
                        draft_stats['rolf_urn'] = self.upload_rofl(rofl_link, game_id, 'scrim_games/')
                    except:
                        rofl_link = None

                    try:
                        proximity_timeline.to_sql('proximity_timeline', engine, index=False, if_exists='append')
                    except exc.SQLAlchemyError as e:
                        print(e)
                        error_df = pd.DataFrame({'error_id': id,
                                                 'sql_error': str(type(e))}, index=[0])
                        error_df.to_csv(self.abs_path+"/data/sql_errors.csv", header=False, mode='a')
                        continue

                try:
                    player_stats.to_sql('player_stats', engine, index=False, if_exists='append')
                    team_stats.to_sql('team_stats', engine, index=False, if_exists='append')
                    draft_stats.to_sql('drafts', engine, index=False, if_exists='append')
                    event_positions.to_sql('event_positions', engine, index=False, if_exists='append')
                    items.to_sql('items', engine, index=False, if_exists='append')
                    runes.to_sql('runes', engine, index=False, if_exists='append')
                    wards.to_sql('wards', engine, index=False, if_exists='append')
                    events.to_sql('events', engine, index=False, if_exists='append')
                except exc.SQLAlchemyError as e:
                    print(e)
                    error_df = pd.DataFrame({'error_id': id, 'sql_error': str(type(e))}, index=[0])
                    error_df.to_csv(self.abs_path+"/data/sql_errors.csv", header=False, mode='a')
