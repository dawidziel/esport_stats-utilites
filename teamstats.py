from get_token import get_token
from functools import reduce
import pandas as pd
import numpy as np
import requests


class TeamStats:
    def __init__(self, df, player_stats):
        self.df = df
        self.player_stats = player_stats
        self.token = get_token()

    def get_teams_urn(self):
        teams = self.df['teams'].iloc[0]
        teams_urn = [x['urn'] for x in teams]

        return teams_urn

    def get_opposite_team_urn(self, team_urn):
        team_list = self.get_teams_urn()

        if team_list[0] == team_urn:
            return team_list[1]
        else:
            return team_list[0]

    def get_your_team_name(self, team_code):
        teams = requests.get(
            'https://lolesports-api.bayesesports.com/scrim/v1/teams',
            headers={"Authorization": f"Bearer {self.token}"}
        )
        team_name = [x['name']
                     for x in teams.json() if x['code'] == team_code][0]

        return team_name

    def get_match_urn(self):
        return self.player_stats['liveDataMatchUrn'].iloc[0]

    def get_league_id(self):
        return self.player_stats['leagueId'].iloc[0]

    def get_game_time(self):
        game_time = self.player_stats.groupby(['liveDataTeamUrn'])[
            'gameTime'].agg(pd.Series.mode).reset_index()
        return game_time

    def get_team_names(self):
        team_names = self.player_stats.groupby(['liveDataTeamUrn'])[
            'teamName'].agg(pd.Series.mode).reset_index()
        team_names['teamName'] = team_names['teamName'].apply(lambda x: x[0] if type(x)!=str else x)
        
        return team_names

    def get_enemy_team_names(self):
        team_names = self.get_team_names()
        team_names['teamName'] = list(team_names['teamName'])[::-1]
        enemy_names = team_names.rename(columns={'teamName': 'enemyName'}).filter([
            'liveDataTeamUrn', 'enemyName'])

        return enemy_names

    def get_first_blood(self):
        player_stats = self.player_stats
        first_blood = player_stats.groupby(['liveDataTeamUrn'])['firstBloodKiller'].sum()

        return first_blood.reset_index()

    def get_patch(self):
        player_stats = self.player_stats
        patch = player_stats['patch'].iloc[0]

        return patch

    def get_result(self):
        player_stats = self.player_stats
        result = player_stats.groupby(['liveDataTeamUrn'])[
            'result'].agg(pd.Series.mode).reset_index()

        return result

    def get_side(self):
        player_stats = self.player_stats
        side = player_stats.groupby(['liveDataTeamUrn'])[
            'side'].agg(pd.Series.mode).reset_index()

        return side

    def get_gold_diff(self):
        player_stats = self.player_stats
        gold_diff_8 = player_stats.groupby(['liveDataTeamUrn'])[
            'goldDiff@8'].sum().reset_index()
        gold_diff_14 = player_stats.groupby(['liveDataTeamUrn'])[
            'goldDiff@14'].sum().reset_index()
        gold_diff = pd.merge(gold_diff_8, gold_diff_14)

        return gold_diff

    def get_resource_percent(self):
        player_stats = self.player_stats
        jungle_sum = player_stats.groupby(['liveDataTeamUrn'])[
            ['neutralMinionsKilled', 'neutralMinionsKilled@14']].sum().reset_index()
        lane_sum = player_stats.groupby(['liveDataTeamUrn'])[['minionsKilled', 'minionsKilled@14']].sum().reset_index()

        jungle_sum['jgl%'] = (jungle_sum['neutralMinionsKilled'] /
                              jungle_sum['neutralMinionsKilled'].sum())
        lane_sum['lne%'] = (lane_sum['minionsKilled'] /
                            lane_sum['minionsKilled'].sum())

        jungle_sum['jgl%@14'] = (jungle_sum['neutralMinionsKilled@14'] /
                                 jungle_sum['neutralMinionsKilled@14'].sum())
        lane_sum['lne%@14'] = (lane_sum['minionsKilled@14'] /
                               lane_sum['minionsKilled@14'].sum())

        resource_percent = pd.merge(jungle_sum, lane_sum, on='liveDataTeamUrn')

        return resource_percent.filter(['liveDataTeamUrn', 'jgl%', 'lne%', 'jgl%@14', 'lne%@14'])

    def get_gold_spent_diff(self):
        player_stats = self.player_stats

        gold_spent = player_stats.groupby(['liveDataTeamUrn'])[
            'goldSpent'].sum().reset_index()
        gold_spent['gspd'] = np.nan

        gold_spent['gspd'].iloc[0] = ((gold_spent['goldSpent'].iloc[0] - gold_spent['goldSpent'].iloc[1]) /
                                      ((gold_spent['goldSpent'].iloc[0] + gold_spent['goldSpent'].iloc[1])/2))
        gold_spent['gspd'].iloc[1] = ((gold_spent['goldSpent'].iloc[1] - gold_spent['goldSpent'].iloc[0]) /
                                      ((gold_spent['goldSpent'].iloc[1] + gold_spent['goldSpent'].iloc[0])/2))

        return gold_spent.filter(['liveDataTeamUrn', 'gspd'])

    def first_drake(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                                     'gameTime': 'firstDrakeKilledTimer',
                                     'dragonType': 'firstDrakeType'})

        drake_df = df[(df['monsterType'] == 'dragon') &
                      (df['action'] == 'KILLED_ANCIENT')].iloc[[0]]
        drake_df = drake_df.filter(
            ['liveDataTeamUrn', 'firstDrakeKilledTimer', 'firstDrakeType'])
        drake_df['firstDrakeKilledTimer'] = drake_df['firstDrakeKilledTimer']/60000
        drake_df.insert(1, 'firstDrake', 1)
        opposite_team_urn = self.get_opposite_team_urn(
            drake_df['liveDataTeamUrn'].iloc[0])
        new_row = {'liveDataTeamUrn': opposite_team_urn, 'firstDrakeKilledTimer': drake_df['firstDrakeKilledTimer'].iloc[0],
                   'firstDrakeType':  drake_df['firstDrakeType'].iloc[0], 'firstDrake': 0}
        drake_df = pd.concat([drake_df, pd.DataFrame(
            new_row, index=[0])], ignore_index=True)

        return drake_df

    def drake_kills(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn', 'monsterType': 'elementalDrakesKilled'})
        elemental_drake_df = df[(df['elementalDrakesKilled'] == 'dragon') & 
                                (df['action'] == 'KILLED_ANCIENT') & (df['dragonType'] != 'elder')]
        elemental_drake_df = elemental_drake_df.groupby(['liveDataTeamUrn'])['elementalDrakesKilled'
                                                                             ].count().reset_index()

        return elemental_drake_df

    def elder_drake_kills(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                                     'monsterType': 'elderDrakesKilled'})
        elder_drake_df = df[(df['elderDrakesKilled'] == 'dragon') & 
                            (df['action'] == 'KILLED_ANCIENT') & 
                            (df['dragonType'] == 'elder')]

        if not elder_drake_df.empty:
            elder_drake_df = elder_drake_df.groupby(['liveDataTeamUrn'])['elderDrakesKilled'
                                                                         ].count().reset_index()
        else:
            team_names = self.get_teams_urn()
            empty_df = pd.DataFrame({'liveDataTeamUrn': [team_names[0], team_names[1]], 
                                     'elderDrakesKilled': [0, 0]}, index=[0, 1])
            elder_drake_df = pd.concat([elder_drake_df, empty_df], ignore_index=True)

            return elder_drake_df.filter(['liveDataTeamUrn', 'elderDrakesKilled'])

        if len(elder_drake_df.index) < 2:
            opposite_team_urn = self.get_opposite_team_urn(
                elder_drake_df['liveDataTeamUrn'].iloc[0])
            new_row = {'liveDataTeamUrn': opposite_team_urn,
                       'elderDrakesKilled': 0}
            elder_drake_df = pd.concat(
                [elder_drake_df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

        return elder_drake_df

    def first_herald(self):
        team_names = self.get_teams_urn()
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn', 
                                     'gameTime': 'firstHeraldKilledTimer'})
        herald_df = df[(df['monsterType'] == 'riftHerald') & (
            df['action'] == 'KILLED_ANCIENT')]
        if not herald_df.empty:
            herald_df = herald_df.iloc[[0]]
            herald_df = herald_df.filter(['liveDataTeamUrn', 
                                          'firstHeraldKilledTimer'])
            herald_df['firstHeraldKilledTimer'] = herald_df['firstHeraldKilledTimer']/60000
            herald_df.insert(1, 'firstHerald', 1)
        else:
            herald_df = pd.DataFrame({'liveDataTeamUrn': [
                                     team_names[0]], 'firstHeraldKilledTimer': [np.nan]}, index=[0])
            herald_df.insert(1, 'firstHerald', 0)

        opposite_team_urn = self.get_opposite_team_urn(
            herald_df['liveDataTeamUrn'].iloc[0])
        new_row = {'liveDataTeamUrn': opposite_team_urn,
                   'firstHeraldKilledTimer': herald_df['firstHeraldKilledTimer'].iloc[0], 'firstHerald': 0}
        herald_df = pd.concat([herald_df, pd.DataFrame(
            new_row, index=[0])], ignore_index=True)

        return herald_df

    def herald_kills(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'monsterType': 'heraldsKilled'})
        herald_df = df[(df['heraldsKilled'] == 'riftHerald') & (
            df['action'] == 'KILLED_ANCIENT')]
        herald_df = herald_df.groupby(['liveDataTeamUrn'])[
            'heraldsKilled'].count().reset_index()

        return herald_df

    def first_baron(self):
        team_names = self.get_teams_urn()
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'gameTime': 'firstBaronKilledTimer'})
        baron_df = df[(df['monsterType'] == 'baron') & (
            df['action'] == 'KILLED_ANCIENT')]
        if not baron_df.empty:
            baron_df = baron_df.iloc[[0]]
            baron_df = baron_df.filter(
                ['liveDataTeamUrn', 'firstBaronKilledTimer'])
            baron_df['firstBaronKilledTimer'] = baron_df['firstBaronKilledTimer']/60000
            baron_df.insert(1, 'firstBaron', 1)
        else:
            baron_df = pd.DataFrame(
                {'liveDataTeamUrn': [team_names[0]], 'firstBaronKilledTimer': [np.nan]}, index=[0])
            baron_df.insert(1, 'firstBaron', 0)

        opposite_team_urn = self.get_opposite_team_urn(
            baron_df['liveDataTeamUrn'].iloc[0])
        new_row = {'liveDataTeamUrn': opposite_team_urn,
                   'firstBaronKilledTimer': baron_df['firstBaronKilledTimer'].iloc[0], 'firstBaron': 0}
        baron_df = pd.concat([baron_df, pd.DataFrame(
            new_row, index=[0])], ignore_index=True)

        return baron_df

    def baron_kills(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'monsterType': 'baronsKilled'})
        baron_df = df[(df['baronsKilled'] == 'baron') & (
            df['action'] == 'KILLED_ANCIENT')]
        baron_df = baron_df.groupby(['liveDataTeamUrn'])[
            'baronsKilled'].count().reset_index()

        if len(baron_df.index) < 1:
            baron_df = pd.DataFrame({'liveDataTeamUrn': self.get_teams_urn()[
                                    0], 'baronsKilled': 0}, index=[0])

        return baron_df

    def first_tower(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'gameTime': 'firstTowerKilledTimer'})
        tower_df = df[(df['buildingType']
                       == 'turret')].iloc[[0]]
        tower_df = tower_df.filter(
            ['liveDataTeamUrn', 'firstTowerKilledTimer'])
        tower_df['firstTowerKilledTimer'] = tower_df['firstTowerKilledTimer']/60000
        tower_df.insert(1, 'firstTower', 1)

        opposite_team_urn = self.get_opposite_team_urn(
            tower_df['liveDataTeamUrn'].iloc[0])
        new_row = {'liveDataTeamUrn': opposite_team_urn,
                   'firstTowerKilledTimer': tower_df['firstTowerKilledTimer'].iloc[0], 'firstTower': 0}
        tower_df = pd.concat([tower_df, pd.DataFrame(
            new_row, index=[0])], ignore_index=True)

        return tower_df

    def first_mid_tower(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'gameTime': 'firstMidTowerKilledTimer'})
        try:
            tower_df = df[(df['buildingType'] == 'turret') & (df['lane'] == 'mid')].iloc[[0]]
        except:
            return pd.DataFrame()

        tower_df = tower_df.filter(['liveDataTeamUrn', 'firstMidTowerKilledTimer'])
        tower_df['firstMidTowerKilledTimer'] = tower_df['firstMidTowerKilledTimer']/60000
        tower_df.insert(1, 'firstMidTower', 1)

        opposite_team_urn = self.get_opposite_team_urn(tower_df['liveDataTeamUrn'].iloc[0])
        new_row = {'liveDataTeamUrn': opposite_team_urn,
                   'firstMidTowerKilledTimer': tower_df['firstMidTowerKilledTimer'].iloc[0], 'firstMidTower': 0}
        tower_df = pd.concat([tower_df, pd.DataFrame(
            new_row, index=[0])], ignore_index=True)

        return tower_df

    def first_to_three_towers(self):
        df = self.df.rename(
            columns={'killerTeamUrn': 'liveDataTeamUrn'})
        tower_df = df[(df['buildingType'] == 'turret')]

        team_names = self.get_teams_urn()
        team_f3t = [0, 0]
        t1 = 0
        t2 = 0
        for row in tower_df.to_dict(orient='records'):
            if row['liveDataTeamUrn'] == team_names[0]:
                t1 += 1
            if row['liveDataTeamUrn'] == team_names[1]:
                t2 += 1
            if t1 == 3:
                team_f3t = [1, 0]
            if t2 == 3:
                team_f3t = [0, 1]

        f3t_df = pd.DataFrame(
            {'liveDataTeamUrn': [team_names[0], team_names[1]], 'f3t': team_f3t}, index=[0, 1])

        return f3t_df

    def turrets_taken(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'buildingTeamUrn': 'turrets'})
        tower_df = df[(df['buildingType'] == 'turret')]
        tower_df = tower_df.groupby(['liveDataTeamUrn'])[
            'turrets'].count().reset_index()

        return tower_df

    # add categories based on turret lane
    def turret_plates_taken(self):
        df = self.df.rename(columns={'killerTeamUrn': 'liveDataTeamUrn',
                            'buildingTeamUrn': 'turretPlates'})
        tower_df = df[(df['buildingType']
                       == 'turretPlate')]
        plates_df = tower_df.groupby(['liveDataTeamUrn'])[
            'turretPlates'].count().reset_index()

        top_plates_df = tower_df[tower_df['lane'] == 'top'].groupby(
            ['liveDataTeamUrn'])['turretPlates'].count().reset_index()
        top_plates_df = top_plates_df.rename(
            columns={'turretPlates': 'topPlates'})
        mid_plates_df = tower_df[tower_df['lane'] == 'mid'].groupby(
            ['liveDataTeamUrn'])['turretPlates'].count().reset_index()
        mid_plates_df = mid_plates_df.rename(
            columns={'turretPlates': 'midPlates'})
        bot_plates_df = tower_df[tower_df['lane'] == 'bot'].groupby(
            ['liveDataTeamUrn'])['turretPlates'].count().reset_index()
        bot_plates_df = bot_plates_df.rename(
            columns={'turretPlates': 'botPlates'})

        plates_df = reduce(lambda left, right: pd.merge(left, right, on=["liveDataTeamUrn"], how="outer"), [
                           plates_df, top_plates_df, mid_plates_df, bot_plates_df])

        return plates_df

    def end_game_stats(self):
        dfs = [self.get_team_names(), self.get_side(), self.get_result(), self.get_game_time(),
               self.get_enemy_team_names(), self.get_first_blood(), self.get_gold_diff(),
               self.first_drake(), self.drake_kills(), self.elder_drake_kills(),
               self.first_herald(), self.herald_kills(), self.first_baron(), self.baron_kills(),
               self.first_tower(), self.first_mid_tower(), self.first_to_three_towers(),
               self.turrets_taken(), self.turret_plates_taken(), self.get_gold_spent_diff(), self.get_resource_percent()]

        teams_df = reduce(lambda left, right: pd.merge(left, right, on=["liveDataTeamUrn"], how="outer") if right.empty == False else left, dfs)
        teams_df.insert(0, 'patch', self.get_patch())
        teams_df.insert(0, 'leagueId', self.get_league_id())
        teams_df.insert(0, 'liveDataMatchUrn', self.get_match_urn())
        teams_df = teams_df.fillna(0)

        return teams_df
