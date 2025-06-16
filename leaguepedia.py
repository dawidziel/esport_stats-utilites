from config import pg_password
import urllib.request
import json
import numpy as np
import mwclient
import pandas as pd
import base64
from sqlalchemy import create_engine, exc
import os

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
PG_PASSWORD = base64.b64decode(pg_password).decode('utf-8')


class Leaguepedia:
    def __init__(self, engine):
        self.engine = engine
        try:
            self.player_role_df = pd.read_sql('Select player_id, id, role from player_info', self.engine)
        except:
            self.player_role_df = pd.DataFrame(
                {'player_id': [None], 'id':[None], 'role': [None]}, index=[0])

    def patch_to_float(self, patch):
        patch = patch.split(".", 2)[:2]
        patch = patch[0] + "." + patch[1]

        if int(patch.split(".")[1]) < 10:
            patchstr = patch.split(".")[0] + ".0" + patch.split(".")[1]
        else:
            patchstr = patch
        return float(patchstr)

    def check_patch(self):
        patches_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        with urllib.request.urlopen(patches_url) as url:
            patches = json.loads(url.read().decode())
        patch = patches[0]

        return patch

    def check_df_patch(self):
        champion_names_df = pd.read_csv(
            PROGRAM_PATH+'\\data\\champion_names_df.csv')
        return champion_names_df['championName'].iloc[0]

    def update_champ_ids(self, last_patch):
        champions_url = 'http://ddragon.leagueoflegends.com/cdn/' + \
            str(last_patch)+'/data/en_US/champion.json'
        last_patch = self.patch_to_float(last_patch)
        champion_names_df = pd.DataFrame(
            {'championID': ['Patch'], 'championName': [last_patch]}, index=[0])

        with urllib.request.urlopen(champions_url) as url:
            champions = json.loads(url.read().decode())
        for champion in champions['data']:
            champion_id = str(champions['data'][champion]['key'])
            champion_name = str(champions['data'][champion]['name'])

            champion_row_df = pd.DataFrame(
                {'championID': champion_id, 'championName': champion_name}, index=[0])
            champion_names_df = pd.concat(
                [champion_names_df, champion_row_df], ignore_index=True)

        champion_names_df.to_csv(PROGRAM_PATH+'\\data\\champion_names_df.csv', index=False)

    # given champ id returns champion name
    def champ_id_to_name(self, champ_id, patch):
        try:
            df_patch = self.check_df_patch()
        except:
            df_patch = 1
        if float(df_patch) < float(patch):
            self.update_champ_ids(self.check_patch())

        try:
            champion_names_df = pd.read_csv(
                PROGRAM_PATH+'\\data\\champion_names_df.csv')
        except:
            self.update_champ_ids(self.check_patch())
            champion_names_df = pd.read_csv(PROGRAM_PATH+'\\data\\champion_names_df.csv')

        return champion_names_df.loc[champion_names_df['championID'] == str(champ_id)]['championName'].iloc[0]

    def check_if_player_exists(self, player_id):
        if self.player_role_df[self.player_role_df['player_id'] == player_id].empty:
            return False
        else:
            return True

    def player_id_to_role(self, player_id):
        # Importing df from player roles file
        if self.check_if_player_exists(player_id):
            try:
                player_role_df = self.player_role_df[self.player_role_df['player_id'] == player_id]
                return player_role_df['role'].iloc[0]
            except:
                return np.NaN
        else:
            return np.NaN
    
    def player_name_to_role(self, player_name):
        try:
            player_role_df = self.player_role_df[self.player_role_df['id'] == player_name]
            
            return player_role_df['role'].iloc[0]
        except:
            return np.NaN

    def new_player_name_to_role(self, player_id, player_name):
        roles = ['Top', 'Mid', 'Jungle', 'Support', 'Bot']
        site = mwclient.Site('lol.fandom.com', path='/')
        response = site.api('cargoquery',
                            limit="max",
                            tables="Players=P",
                            fields="P.ID, P.Player, P.Name, P.Role, P.Team, P.Residency, P.Lolpros",
                            where='P.ID =  "%s" and P.IsRetired = "No"' % player_name
                            )
        player_info_response = json.dumps(response)
        player_info = json.loads(player_info_response)
        if self.check_if_player_exists(player_id):
            return np.NaN
        else:
            if len(player_info['cargoquery']) > 1:
                player_info = [
                    x for x in player_info['cargoquery'] if x['title']['Role'] in roles][0]
            else:
                try:
                    player_info = player_info['cargoquery'][0]
                except:
                    player_info = {}

            try:
                player_info_df = pd.DataFrame(player_info['title'], index=[0])
                player_info_df.columns = player_info_df.columns.str.lower()
                player_info_df.insert(0, 'player_id', player_id)
                try:
                    player_info_df.to_sql('player_info', self.engine,
                                          index=False, if_exists='append')
                except exc.SQLAlchemyError as e:
                    print("SQL ERROR FOR player: %s" %
                          player_name + str(type(e)))
                return player_info['title']['Role']
            except:
                return np.NaN

    # function to get updated player ID (when old one was used)
    def old_to_new_id_name(self, player_name):
        roles = ['Top', 'Mid', 'Jungle', 'Support', 'Bot']
        site = mwclient.Site('lol.fandom.com', path='/')
        response = site.api('cargoquery',
                            limit="max",
                            tables="PlayerRedirects=PR, Players=P",
                            join_on="P.OverviewPage=PR.OverviewPage",
                            fields="PR.AllName, PR.OverviewPage, PR.ID, P.Role",
                            where='PR.ID =  "%s"' % player_name
                            )
        player_info_response = json.dumps(response)
        player_info = json.loads(player_info_response)
        if len(player_info['cargoquery']) > 1:
            player_info = [
                x for x in player_info['cargoquery'] if x['title']['Role'] in roles][0]
        else:
            try:
                player_info = player_info['cargoquery'][0]
            except:
                player_info = {}

        try:
            new_player_name = player_info['title']['OverviewPage']
            return new_player_name.split(" (")[0]
        except:
            return np.NaN
