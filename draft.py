from leaguepedia import Leaguepedia
import pandas as pd
pd.options.mode.chained_assignment = None


class DraftData:
    def __init__(self, df, team_stats, player_stats, engine):
        self.df = df
        self.L = Leaguepedia(engine)
        self.player_stats = player_stats
        self.team_stats = team_stats

    def get_info(self):
        team_stats = self.team_stats

        if team_stats.loc[team_stats['side'] == 'blue']['result'].iloc[0] == '1':
            winner_team = 1
        elif team_stats.loc[team_stats['side'] == 'red']['result'].iloc[0] == '1':
            winner_team = 2
        else:
            winner_team = '-'

        info = {'liveDataMatchUrn': team_stats['liveDataMatchUrn'].iloc[0],
                'patch': team_stats['patch'].iloc[0],
                'blueTeamUrn': team_stats.loc[team_stats['side'] == 'blue']['liveDataTeamUrn'].iloc[0],
                'redTeamUrn':  team_stats.loc[team_stats['side'] == 'red']['liveDataTeamUrn'].iloc[0],
                'blueTeamName': team_stats.loc[team_stats['side'] == 'blue']['teamName'].iloc[0],
                'redTeamName': team_stats.loc[team_stats['side'] == 'red']['teamName'].iloc[0],
                'winnerTeam': winner_team}

        return info

    def get_bans(self):
        df = self.df[(self.df['subject'] == 'TEAM') & (
            self.df['action'] == 'UPDATE')]['bannedChampions'].iloc[-1]
        bans_df = pd.DataFrame(df)
        patch = self.player_stats['patch'].iloc[0]

        
        pick_turn_dict = {'BB1': [1, 100], 'RB1': [2, 200], 'BB2': [3, 100], 'RB2': [4, 200],
                          'BB3': [5, 100], 'RB3': [6, 200], 'RB4': [1, 200], 'BB4': [2, 100],
                          'RB5': [3, 200], 'BB5': [4, 100]}
        
        def get_champion_pick(pick_turn, team_id):
            id_df = bans_df.loc[(bans_df['pickTurn'] == pick_turn) & (bans_df['teamId'] == team_id), 'championId']

            if id_df.empty:
                return None
            else:
                return self.L.champ_id_to_name(id_df.iloc[0], patch)

        bans_dict = {k: get_champion_pick(v[0], v[1]) for (k, v) in pick_turn_dict.items()}

        return bans_dict

    def get_picks(self):
        df = self.df[(self.df['action'] == 'SELECTED_HERO')
                     ].drop_duplicates('championId').filter(['championId'])
        index_list = ['B1', 'R1', 'R2', 'B2',
                      'B3', 'R3', 'R4', 'B4', 'B5', 'R5']

        df['index'] = index_list
        df = df.set_index('index')
        patch = self.team_stats['patch'].iloc[0]
        picks_dict = df.T.to_dict(orient='records')[0]

        picks_dict = {k: self.L.champ_id_to_name(int(v), patch) for (k, v) in picks_dict.items()}


        return picks_dict

    def get_role_from_champ_id(self, champ_name):
        try:
            role = self.player_stats[(self.player_stats['championName'] == champ_name)]['role'].iloc[0]
        except:
            role = ''
        return role

    def get_roles(self):
        picks_dict = self.get_picks()
        role_dict = {k+'Role': self.get_role_from_champ_id(v) for (k, v) in picks_dict.items()}

        return role_dict

    def get_draft(self):
        info = self.get_info()
        picks = self.get_picks()
        roles = self.get_roles()
        try:
            bans = self.get_bans()
        except:
            bans = {}

        # merging dicts to one
        info |= bans
        info |= picks
        info |= roles
        drafts = pd.DataFrame(info, index=[0])
        drafts['date'] = self.player_stats['date']

        return drafts
