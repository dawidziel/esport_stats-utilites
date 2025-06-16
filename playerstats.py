from positiontables import PositionTables
from leaguepedia import Leaguepedia
import pandas as pd
import numpy as np
from config import *
import re


class PlayerStats:
    def __init__(self, df, engine, id):
        self.df = df
        self.engine = engine
        self.id = id

    def is_nan(self, string):
        return string != string

    # returns game duration in minutes
    def game_time(self):
        df = self.df
        df = df.drop(df[(df['action'] != "UPDATE")].index)
        df = df.iloc[[-1]]

        game_time = df['gameTime']

        return float(int(game_time)/60000)

    def del_team_tag(self, player_name):
        if len(player_name.split(" ", 1)) == 1:
            return str(player_name)
        else:
            return str(player_name.split(" ", 1)[1])

    def game_id(self):
        return self.df['liveDataMatchUrn'].iloc[0]

    # returns patch the game has been played on
    def game_version(self):
        df = self.df
        df = df.drop(df[(df['action'] != "UPDATE")].index)
        df = df.iloc[-1]

        patch = df['gameVersion'].split(".", 2)[:2]
        patch = patch[0] + "." + patch[1]

        if int(patch.split(".")[1]) < 10:
            patchstr = patch.split(".")[0] + ".0" + patch.split(".")[1]
        else:
            patchstr = patch

        return patchstr

    # returns if the team provided has won the game
    def result(self, team_nr):
        df = self.df
        df = df.drop(df[(df['action'] != "UPDATE")].index)
        df = df.iloc[[-1]]

        if team_nr == 'teamOne':
            team_nr = 100
        elif team_nr == 'teamTwo':
            team_nr = 200

        winning_team = int(df['winningTeam'])

        if winning_team == team_nr:
            return '1'
        elif winning_team == 0:
            return '-'
        else:
            return '0'

    def first_blood(self):
        df = self.df
        df = df.drop(df[(df['action'] != "KILL")].index)
        first_blood_killer = df['killerUrn'].iloc[0]
        first_blood_participant = df['assistants'].iloc[0]

        return first_blood_killer, first_blood_participant

    def lvl6_timer(self):
        df = self.df
        df = df[(df['action'] == "LEVEL_UP") &
                (df['newValue'] == 6)]
        lvl6_df = df.filter(
            ['playerUrn', 'gameTime'])

        return lvl6_df

    def player_stats_minute(self, player_roles_df, minute):
        df = self.df
        df['gameTime'] = df['gameTime'].astype(float)
        df = df.drop(df[(df['action'] != "UPDATE")].index).reset_index()

        minute_index = abs(df['gameTime'] - (minute * 60000)).idxmin()
        df = df.iloc[minute_index]

        playerDfOne = pd.DataFrame(df['teamOne.players'])
        playerDfTwo = pd.DataFrame(df['teamTwo.players'])
        playerDfboth = pd.concat([playerDfOne, playerDfTwo], ignore_index=True)
        playerDfboth = pd.merge(playerDfboth, player_roles_df, on="liveDataPlayerUrn")

        player_stats_df_both = pd.DataFrame(list(playerDfboth['stats']))
        player_stats_df_both['kills@'+str(minute)], player_stats_df_both['assists@'+str(minute)] = [np.nan, np.nan]
        player_stats_df_both['deaths@'+str(minute)], player_stats_df_both['kills_assists@'+str(minute)] = [np.nan, np.nan]
        player_stats_df_both['cs@'+str(minute)], player_stats_df_both['gold@' +
                                                                      str(minute)] = [np.nan, np.nan]
        player_stats_df_both['xp@'+str(minute)], player_stats_df_both['goldDiff@'+str(minute)] = [np.nan, np.nan]
        player_stats_df_both['csDiff@'+str(minute)], player_stats_df_both['xpDiff@'+str(minute)] = [np.nan, np.nan]
        player_stats_df_both['minionsKilled@'+str(minute)], player_stats_df_both['neutralMinionsKilled@'+str(minute)] = [np.nan, np.nan]

        for x in range(0, 10):
            # player_stats_df_both = pd.concat([player_stats_df_both, pd.DataFrame(playerDfboth['stats'][x])], ignore_index=True)
            player_stats_df_both['gold@' + str(minute)].iloc[x] = playerDfboth['totalGold'][x]
            player_stats_df_both['xp@' + str(minute)].iloc[x] = playerDfboth['experience'][x]
            player_stats_df_both['kills@'+str(minute)].iloc[x] = int(player_stats_df_both.iloc[x]['championsKilled'])
            player_stats_df_both['assists@'+str(minute)].iloc[x] = int(player_stats_df_both.iloc[x]['assists'])
            player_stats_df_both['kills_assists@'+str(minute)].iloc[x] = (int(player_stats_df_both.iloc[x]['championsKilled']) + 
                                                                          int(player_stats_df_both.iloc[x]['assists']))
            player_stats_df_both['deaths@'+str(minute)].iloc[x] = int(
                player_stats_df_both.iloc[x]['numDeaths'])
            player_stats_df_both['cs@'+str(minute)].iloc[x] = int(round(float(
                player_stats_df_both.iloc[x]['minionsKilled'])+float(player_stats_df_both.iloc[x]['neutralMinionsKilled'])))
            player_stats_df_both['minionsKilled@'+str(minute)].iloc[x] = float(
                player_stats_df_both.iloc[x]['minionsKilled'])
            player_stats_df_both['neutralMinionsKilled@'+str(minute)].iloc[x] = float(
                player_stats_df_both.iloc[x]['neutralMinionsKilled'])

        player_stats_df_both.insert(0, 'role', playerDfboth['role'])
        player_stats_df_both.insert(0, 'liveDataPlayerUrn', playerDfboth['liveDataPlayerUrn'])

        # calculate cs, gold and xp differences
        for x in range(0, 10):
            for y in range(x+1, 10):
                if player_stats_df_both['role'].iloc[x] == player_stats_df_both['role'].iloc[y]:
                    player_stats_df_both['goldDiff@'+str(minute)].iloc[x] = player_stats_df_both['gold@'+str(
                        minute)].iloc[x] - player_stats_df_both['gold@'+str(minute)].iloc[y]
                    player_stats_df_both['csDiff@'+str(minute)].iloc[x] = player_stats_df_both['cs@'+str(
                        minute)].iloc[x] - player_stats_df_both['cs@'+str(minute)].iloc[y]
                    player_stats_df_both['xpDiff@'+str(minute)].iloc[x] = player_stats_df_both['xp@'+str(
                        minute)].iloc[x] - player_stats_df_both['xp@'+str(minute)].iloc[y]

                    player_stats_df_both['goldDiff@'+str(
                        minute)].iloc[y] = - player_stats_df_both['goldDiff@'+str(minute)].iloc[x]
                    player_stats_df_both['csDiff@'+str(
                        minute)].iloc[y] = - player_stats_df_both['csDiff@'+str(minute)].iloc[x]
                    player_stats_df_both['xpDiff@'+str(
                        minute)].iloc[y] = - player_stats_df_both['xpDiff@'+str(minute)].iloc[x]

        return player_stats_df_both.iloc[:, -12:]

    def role_proximity_diff(self, proximity_percentage):
        prox_diff_df = proximity_percentage
        prox_diff_df['suppProxDiff'], prox_diff_df['jungleProxDiff'] = [np.nan, np.nan]

        for player in prox_diff_df.to_dict(orient='records'):
            try:
                prox_diff_df.loc[(prox_diff_df['liveDataPlayerUrn'] == player['liveDataPlayerUrn']), 'suppProxDiff'] = (
                    float(prox_diff_df[prox_diff_df['liveDataPlayerUrn'] == player['liveDataPlayerUrn']]["Support"]) -
                    float(prox_diff_df[(prox_diff_df['role'] == player['role']) & (prox_diff_df['liveDataTeamUrn'] != player['liveDataTeamUrn'])]['Support']))
            except:
                prox_diff_df.loc[(prox_diff_df['liveDataPlayerUrn']
                                  == player['liveDataPlayerUrn']), 'suppProxDiff'] = 0

            try:
                prox_diff_df.loc[(prox_diff_df['liveDataPlayerUrn'] == player['liveDataPlayerUrn']), 'jungleProxDiff'] = (
                    float(prox_diff_df[prox_diff_df['liveDataPlayerUrn'] == player['liveDataPlayerUrn']]["Jungle"]) -
                    float(prox_diff_df[(prox_diff_df['role'] == player['role']) & (prox_diff_df['liveDataTeamUrn'] != player['liveDataTeamUrn'])]['Jungle']))
            except:
                prox_diff_df.loc[(prox_diff_df['liveDataPlayerUrn'] ==
                                  player['liveDataPlayerUrn']), 'jungleProxDiff'] = 0

        prox_diff_df = prox_diff_df.rename(columns={"Support": "supportProx", 
                                                    "Jungle": "jungleProx"})

        return prox_diff_df.filter(['liveDataPlayerUrn', 'supportProx', 'jungleProx', 'suppProxDiff', 'jungleProxDiff'])

    # returns player statistics
    def player_stats(self, team_nr):
        end_df = self.df[(self.df['action'] == "UPDATE")].iloc[-1]
        date = self.df['sourceUpdatedAt'].iloc[0]
        match_id = end_df['liveDataMatchUrn']
        esports_game_id = self.id
        team_id = end_df[''+team_nr+'.liveDataTeamUrn']
        try:
            self.league_id = end_df['additionalProperties.esportsLeagueId']
        except:
            self.league_id = "SCRIM"

        lvl6_df = self.lvl6_timer()
        game_duration = self.game_time()
        patch = self.game_version()
        score = self.result(team_nr)
        first_blood_killer = self.first_blood()[0]
        first_blood_participant = self.first_blood()[1]

        playerDf = pd.DataFrame(end_df[''+team_nr+'.players'])
        playerStatsDf = pd.DataFrame(list(playerDf['stats']))
        playerStatsDf.insert(0, 'goldSpent', np.nan)
        playerStatsDf.insert(0, 'goldTotal', np.nan)
        playerStatsDf.insert(0, 'goldShare', np.nan)
        playerStatsDf.insert(0, 'damageShare', np.nan)
        playerStatsDf.insert(0, 'cs/m', np.nan)
        playerStatsDf.insert(0, 'cs', np.nan)
        playerStatsDf.insert(0, 'teamName', np.nan)
        playerStatsDf.insert(0, 'leagueId', np.nan)
        playerStatsDf.insert(0, 'liveDataTeamUrn', np.nan)
        playerStatsDf.insert(0, 'esportsGameId', np.nan)
        playerStatsDf.insert(0, 'liveDataMatchUrn', np.nan)

        # prepping goldshare and damageshare
        team_dmg = 0
        team_gold = 0
        for x in range(0, 5):
            team_dmg += int(playerStatsDf.iloc[x]['totalDamageDealtChampions'])
            team_gold += int(playerDf.iloc[x]['totalGold'])

        for x in range(0, 5):
            playerStatsDf['teamName'].iloc[x] = playerDf['summonerName'].iloc[x].split(" ")[0]
            playerStatsDf['liveDataMatchUrn'].iloc[x] = match_id
            playerStatsDf['esportsGameId'].iloc[x] = esports_game_id
            playerStatsDf['liveDataTeamUrn'].iloc[x] = team_id
            playerStatsDf['leagueId'].iloc[x] = self.league_id
            playerStatsDf['cs'].iloc[x] = int(round(float(playerStatsDf.iloc[x]['minionsKilled'])+
                                                    float(playerStatsDf.iloc[x]['neutralMinionsKilled'])))
            playerStatsDf['cs/m'].iloc[x] = float(round(float(playerStatsDf.iloc[x]['minionsKilled'])+
                                                        float(playerStatsDf.iloc[x]['neutralMinionsKilled'])))/game_duration
            playerStatsDf['goldShare'].iloc[x] = int(playerDf.iloc[x]['totalGold'])/team_gold
            playerStatsDf['goldSpent'].iloc[x] = (int(playerDf.iloc[x]['totalGold']) - 
                                                  int(playerDf.iloc[x]['currentGold']))
            playerStatsDf['goldTotal'].iloc[x] = int(playerDf.iloc[x]['totalGold'])
            playerStatsDf['damageShare'].iloc[x] = int(playerStatsDf.iloc[x]['totalDamageDealtChampions'])/team_dmg

        # filtering original database and prepping to merge with stats
        playerDf = playerDf.filter(['liveDataPlayerUrn', 'teamID', 
                                    'summonerName', 'championID'])
        playerDf.rename(columns={'teamID': 'side'}, inplace=True)
        playerDf.insert(4, "role", np.nan)
        playerDf.insert(5, "firstBloodKiller", 0)
        playerDf.insert(6, "firstBloodParticipant", 0)
        playerDf.insert(7, "lvl6Timer", 0)

        L = Leaguepedia(self.engine)
        # filling game data for players
        for x in range(0, 5):
            playerDf['championID'].iloc[x] = L.champ_id_to_name(playerDf['championID'].iloc[x], 
                                                                patch)
            player_id = playerDf['liveDataPlayerUrn'].iloc[x]
            player_name = self.del_team_tag(playerDf['summonerName'].iloc[x])
            if player_name[0] == ' ': player_name=player_name[1:]

            # this nested conditions are used to determine role of player from leaguepedia based on multiple conditions
            if pd.isna((role := L.player_id_to_role(player_id))) == False:
                playerDf['role'].iloc[x] = role
            elif pd.isna((role := L.player_name_to_role(player_name))) == False:
                playerDf['role'].iloc[x] = role
            elif pd.isna((role := L.new_player_name_to_role(player_id, player_name))) == False:
                playerDf['role'].iloc[x] = role
            elif pd.isna((name := L.old_to_new_id_name(player_name))) == False:
                playerDf['role'].iloc[x] = L.new_player_name_to_role(player_id, name)
            else:
                playerDf['role'].iloc[x] = np.NaN

            if playerDf['side'].iloc[x] == 100:
                playerDf['side'].iloc[x] = 'blue'
            else:
                playerDf['side'].iloc[x] = 'red'

            # adding first blood stats
            if playerDf['liveDataPlayerUrn'].iloc[x] == first_blood_killer:
                playerDf['firstBloodKiller'].iloc[x], playerDf['firstBloodParticipant'].iloc[x] = 1, 1
            if playerDf['liveDataPlayerUrn'].iloc[x] in first_blood_participant:
                playerDf['firstBloodParticipant'].iloc[x] = 1

            # adding lvl6 timer stat
            row = lvl6_df.loc[lvl6_df['playerUrn'] == playerDf['liveDataPlayerUrn'].iloc[x]]
            try:
                playerDf['lvl6Timer'].iloc[x] = float(row['gameTime'].iloc[0])/60000
            except:
                print(lvl6_df)

        # merging dfs together
        mergedDf = playerDf.merge(
            playerStatsDf, left_index=True, right_index=True)

        # adding columns
        mergedDf.insert(6, 'gameTime', game_duration)
        mergedDf.insert(6, 'result', score)
        mergedDf.insert(3, 'patch', patch)
        mergedDf.insert(2, 'date', date)

        # changing names to convention
        mergedDf = mergedDf.rename(columns={"championID": "championName", 
                                            "totalTimeCCOthers": "total_time_cc_others"})

        return mergedDf

    def end_game_stats(self):
        # getting end game player data
        df_team_one = self.player_stats('teamOne')
        df_team_two = self.player_stats('teamTwo')
        df_both_teams = pd.concat([df_team_one, df_team_two], ignore_index=True)

        # initalizing stats from timestamp
        player_roles_df = df_both_teams.filter(items=['liveDataPlayerUrn', 'role', 
                                                      'summonerName', 'championName'])

        # ending method if there is player without assigned role
        roles = ['Top', 'Mid', 'Jungle', 'Support', 'Bot']
        result = all(elem in roles for elem in player_roles_df['role'].values.tolist())

        if result == False:
            faulty_players = player_roles_df[~player_roles_df['role'].isin(roles)]
            faulty_players = faulty_players.filter(['summonerName', 'liveDataPlayerUrn']).rename(columns={
                                                    'liveDataPlayerUrn': 'live_data_player_urn',
                                                    'summonerName': 'summoner_name'})
            faulty_players['league_id'] = self.league_id

            return faulty_players, player_roles_df

        # checking if proximity table will go through, if not return id
        try:
            side = df_both_teams.groupby(['liveDataTeamUrn'])['side'].agg(pd.Series.mode)
            Pos = PositionTables(self.df, player_roles_df, side.to_dict())
            wards = Pos.get_wards()
            event_positions, events = Pos.event_positions()
            proximity_timeline, proximity_percentage = Pos.role_proximity()
        except:
            faulty_game = pd.DataFrame({'summoner_name': 'proximity_error', 
                                        'league_id': self.league_id}, index=[0])
            return faulty_game, player_roles_df

        # merging proximity stats with the rest
        proximity_diff = self.role_proximity_diff(proximity_percentage)
        df_both_teams = df_both_teams.merge(proximity_diff, on="liveDataPlayerUrn")

        # merging dfs with stats
        player_stats_8 = self.player_stats_minute(player_roles_df, 8)
        player_stats_14 = self.player_stats_minute(player_roles_df, 14)
        player_stats_merged = player_stats_8.merge(player_stats_14, left_index=True, right_index=True)
        df_both_teams = df_both_teams.merge(player_stats_merged, left_index=True, right_index=True)
        df_both_teams['patch'] = df_both_teams['patch'].astype(float)
        df_both_teams = df_both_teams.drop('perks', axis=1)

        return df_both_teams, proximity_timeline, event_positions, wards, events
