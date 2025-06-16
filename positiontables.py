import pandas as pd
import math
import re


class PositionTables:
    def __init__(self, df, player_roles, side):
        self.df = df
        self.player_roles = player_roles
        self.side = side
        self.match_id = df['liveDataMatchUrn'].iloc[0]

    def role_proximity(self):
        df = self.df[(self.df['action'] == "UPDATE_POSITIONS") & (self.df['gameTime'] < 900100) & (self.df['gameTime'] > 180000)]
        player_roles_df = self.player_roles

        proximity_dict = {
            'time': [None], 'liveDataMatchUrn': [None], 'liveDataTeamUrn': [None], 'liveDataPlayerUrn': [None], 'side': [None],
            'role': [None], 'playerLocationX': [None], 'playerLocationY': [None], 'Support': [None], 'Jungle': [None]
        }

        for row in df.to_dict(orient="records"):
            temp_df = pd.DataFrame(row['positions'])
            current_time = row['gameTime']
            position_dict = {}
            players = []
            positions = []
            teams = []

            # creating dict with player positions
            for row2 in temp_df.to_dict(orient="records"):
                players.append(row2['playerUrn'])
                positions.append(row2['position'])
                teams.append(row2['teamUrn'])

            for i in range(len(players)):
                temp_player_role = player_roles_df[(
                    player_roles_df['liveDataPlayerUrn'] == players[i])]['role'].iloc[0]
                position_dict[players[i]] = [
                    temp_player_role, positions[i], teams[i]]

            # creating dict that will store bools about player proximity
            for player in position_dict:
                proximity_dict['time'].append(current_time)
                proximity_dict['liveDataMatchUrn'].append(self.match_id)
                proximity_dict['liveDataTeamUrn'].append(position_dict[player][2])
                proximity_dict['side'].append(self.side[position_dict[player][2]])
                proximity_dict['liveDataPlayerUrn'].append(player)
                proximity_dict['role'].append(position_dict[player][0])
                proximity_dict['playerLocationX'].append(position_dict[player][1][0])
                proximity_dict['playerLocationY'].append(position_dict[player][1][1])

                support_keys = [k for k, v in position_dict.items(
                ) if v[0] == "Support" and v[2] == position_dict[player][2]]
                jungle_keys = [k for k, v in position_dict.items(
                ) if v[0] == "Jungle" and v[2] == position_dict[player][2]]

                if (math.dist(position_dict[player][1], position_dict[support_keys[0]][1])
                        < 2000 and position_dict[player][0] != position_dict[support_keys[0]][0]):
                    proximity_dict["Support"].append(1)
                else:
                    proximity_dict["Support"].append(0)

                if (math.dist(position_dict[player][1], position_dict[jungle_keys[0]][1])
                        < 2000 and position_dict[player][0] != position_dict[jungle_keys[0]][0]):
                    proximity_dict["Jungle"].append(1)
                else:
                    proximity_dict["Jungle"].append(0)

        proximity_df = pd.DataFrame(proximity_dict)
        proximity_df = proximity_df.iloc[1:]

        for row in proximity_df.to_dict(orient='records'):
            if row['role'] == 'Support':
                xd = proximity_df.loc[(proximity_df['time'] == row['time']) & (proximity_df['liveDataTeamUrn'] == row['liveDataTeamUrn'])]
                temp_supp_proximity = xd['Support'].sum()

                if temp_supp_proximity != 0:
                    proximity_df.loc[(proximity_df['time'] == row['time']) & (proximity_df['role'] == 'Support') &
                                     (proximity_df['liveDataTeamUrn'] == row['liveDataTeamUrn']), 'Support'] = 1

            elif row['role'] == 'Jungle':
                xd = proximity_df.loc[(proximity_df['time'] == row['time']) & (
                    proximity_df['liveDataTeamUrn'] == row['liveDataTeamUrn'])]
                temp_jungle_proximity = xd['Jungle'].sum()

                if temp_jungle_proximity != 0:
                    proximity_df.loc[(proximity_df['time'] == row['time']) & (proximity_df['role'] == 'Jungle') &
                                     (proximity_df['liveDataTeamUrn'] == row['liveDataTeamUrn']), 'Jungle'] = 1

        proximity_percentage = (proximity_df.groupby(["liveDataPlayerUrn", 'liveDataTeamUrn', "role"]).sum() /
                                len(proximity_df.index)*10).filter(["liveDataPlayerUrn", "role", "Support", "Jungle"])

        return proximity_df, proximity_percentage.reset_index()

    def event_positions(self):
        alive_df = self.df[(self.df['action']== "UPDATE")].filter(['gameTime', 'teamOne.players', 'teamTwo.players'])
        objectives = self.get_event_timers()
        objectives['blueGoldSpent'] = None
        objectives['redGoldSpent'] = None
        player_roles_df = self.player_roles
        side_swap = {v: k for k, v in self.side.items()}
        position_dict = {'liveDataMatchUrn': [None], 'time': [None], 'liveDataTeamUrn': [None], 
                         'liveDataPlayerUrn': [None], 'side': [None],'championName': [None],
                         'alive': [None], 'playerLocationX': [None], 
                         'playerLocationY': [None], 'objectiveId': [None]}
        

        for objective in objectives.to_dict(orient='records'):
            gold_spent = {k:0 for k in self.side}
            df = self.df[(self.df['action'] == "UPDATE_POSITIONS") &
                         (self.df['gameTime'] <= objective['gameTime'] + 2000) &
                         (self.df['gameTime'] >= objective['gameTime'] - 40000)].iloc[::20, :]

            x = 0
            for row in df.to_dict(orient='records'):
                x += 1
                current_time = row['gameTime']
                temp_alive_df = pd.concat([pd.DataFrame(alive_df.loc[alive_df['gameTime'] == 
                                                                    current_time]['teamOne.players'].iloc[0]),
                                          pd.DataFrame(alive_df.loc[alive_df['gameTime'] == 
                                                                    current_time]['teamTwo.players'].iloc[0])])

                temp_df = pd.DataFrame(row['positions'])
                for player in temp_df.to_dict(orient='records'):
                    position_dict['time'].append(current_time)
                    position_dict['liveDataMatchUrn'].append(self.match_id)
                    position_dict['liveDataTeamUrn'].append(player['teamUrn'])
                    position_dict['side'].append(self.side[player['teamUrn']])
                    position_dict['championName'].append(player_roles_df[(player_roles_df['liveDataPlayerUrn'] == 
                                                                          player['playerUrn'])]['championName'].iloc[0])
                    position_dict['alive'].append(temp_alive_df[(temp_alive_df['liveDataPlayerUrn'] == 
                                                                 player['playerUrn'])]['alive'].iloc[0])
                    position_dict['liveDataPlayerUrn'].append(player['playerUrn'])
                    position_dict['playerLocationX'].append(player['position'][0])
                    position_dict['playerLocationY'].append(player['position'][1])
                    position_dict['objectiveId'].append(objective['objectiveId'])
                    if x == 3:
                        gold_spent[player['teamUrn']] += (temp_alive_df[(temp_alive_df['liveDataPlayerUrn'] == 
                                                                         player['playerUrn'])]['totalGold'].iloc[0] - 
                                                          temp_alive_df[(temp_alive_df['liveDataPlayerUrn'] == 
                                                                         player['playerUrn'])]['currentGold'].iloc[0])

            objectives.loc[objectives['objectiveId'] == objective['objectiveId'], 'blueGoldSpent'] = gold_spent[side_swap['blue']]
            objectives.loc[objectives['objectiveId'] == objective['objectiveId'], 'redGoldSpent'] = gold_spent[side_swap['red']]

        return pd.DataFrame(position_dict).iloc[1:], objectives

    def get_event_timers(self):
        df = self.df
        objectives = ['baron', 'dragon', 'riftHerald', 'turret']
        df['objectiveType'] = df['lane'].astype(str) + '_' + df['turretTier'].astype(str)
        
        # getting info about took ancients to df
        ancient_df = df[(df['action'] == 'KILLED_ANCIENT') &
                          (df['monsterType'].isin(objectives))]
        ancient_df = ancient_df.filter(['gameTime', 'monsterType',
                                        'dragonType', 'position', 
                                        'killerTeamUrn'])

        # getting info about took turrets to df
        turret_df = df[(df['action'] == 'TOOK_OBJECTIVE') & 
                       (df['buildingType'] == 'turret')]
        turret_df = turret_df.filter(['gameTime', 'buildingType', 'objectiveType', 
                                      'position', 'killerTeamUrn'])

        # adding turrets to took objectives df
        ancient_df = ancient_df.rename(columns={'dragonType': 'objectiveType', 'monsterType': 'objectiveName'})
        turret_df = turret_df.rename(columns={'buildingType': 'objectiveName'})
        objective_df = pd.concat([ancient_df, turret_df], ignore_index=True).sort_values(by=['gameTime'])

        # getting number for every objective
        ancient_dict = dict.fromkeys(objectives, 1)
        ancient_numbers_list = []
        for row in objective_df.to_dict(orient='records'):
            ancient_numbers_list.append(ancient_dict[row['objectiveName']])
            ancient_dict[row['objectiveName']] += 1

        # adding objective number as column
        objective_df['objectiveNr'] = ancient_numbers_list
        objective_df.insert(0, "liveDataMatchUrn", self.match_id)
        objective_df.insert(1, "objectiveId", objective_df['objectiveName'] + 
                            "_" + objective_df["objectiveNr"].astype(str))
        objective_df[['positionX','positionY']] = pd.DataFrame(
            objective_df['position'].to_list(), columns=['positionX','positionY'])

        objective_df = pd.concat([pd.DataFrame({'liveDataMatchUrn': self.match_id, 'objectiveId': 'lvl1', 
                                                'gameTime': 80000, 'objectiveName': 'lvl1',
                                                'objectiveType': None, 'objectiveNr': None, 
                                                'killerTeamUrn': None, 'positionX': None, 'positionY': None},
                                               index=[0]), objective_df]).drop(columns=['position'])

        return objective_df

    def get_wards(self):
        try:
            wards_df = self.df[self.df['action'].isin(['PLACED_WARD','KILLED_WARD'])]
            wards_df = wards_df.filter(['gameTime', 'action', 'position', 
                                        'wardType', 'placerUrn', 'placerTeamUrn'])

            role_dict = self.player_roles.filter(['liveDataPlayerUrn', 'role']).to_dict(orient='dict')
            role_dict = {}
            for row in self.player_roles.to_dict(orient='records'):
                role_dict.update({row['liveDataPlayerUrn']: row['role']})

            wards_df.insert(0, 'liveDataMatchUrn', self.match_id)
            wards_df[['positionX','positionY']] = pd.DataFrame(
                wards_df['position'].to_list(), columns=['positionX','positionY'])
            wards_df = wards_df.replace({'placerUrn': role_dict}).drop(columns=['position'])
        except:
            wards_df = pd.DataFrame()

        return wards_df
