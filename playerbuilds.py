import pandas as pd
import numpy as np
import math
import re


class PlayerBuilds:
    def __init__(self, df, player_stats):
        self.df = df
        self.match_id = self.df['liveDataMatchUrn'].iloc[0]
        self.player_stats = player_stats
        self.build_df = self.get_end_build()

    def get_end_build(self):
        end_df = self.df[self.df['action'] == 'UPDATE'].iloc[-1]
        build_df_one = pd.DataFrame(end_df['teamOne.players'])
        build_df_two = pd.DataFrame(end_df['teamTwo.players'])
        build_df = pd.concat([build_df_one, build_df_two], ignore_index=True)
        
        return build_df
    
    def get_items(self):
        trinkets = [1104, 3330, 3340, 3363, 3364, 3513]
        items = pd.DataFrame()
        
        for row in self.build_df.to_dict(orient='records'):
            temp_items = pd.DataFrame(row['items'])
            trinket = temp_items[temp_items['itemID'].isin(trinkets)]['itemID'].iloc[0]
            temp_items = temp_items[~temp_items['itemID'].isin(trinkets)].reset_index(drop=True)
            temp_items_timer = temp_items.T.reset_index(drop=True).iloc[[2]]
            temp_items = temp_items.T.reset_index(drop=True).iloc[[0]]

            for x in range(0,6):
                if x not in temp_items:
                    temp_items[x] = np.NaN

                try:
                    temp_items['item_'+str(x)+'_timer'] = temp_items_timer[x].iloc[0]
                except:
                    temp_items['item_'+str(x)+'_timer'] = np.NaN

            temp_items.insert(0, 'live_data_match_urn', self.match_id)
            temp_items.insert(1, 'live_data_player_urn', row['liveDataPlayerUrn'])
            temp_items['trinket'] = trinket
            items = pd.concat([items, temp_items])

        items = items.reset_index(drop=True)
        items.columns = [re.sub('^[0-9]', 'item_'+str(c), str(c)) for c in items.columns]
        
        return items
        
    def get_runes(self):
        runes = pd.DataFrame()
        for row in self.build_df.to_dict(orient='records'):
            perks = pd.DataFrame(row['stats']['perks'])

            perks_temp = {}
            rc = 0
            for row2 in perks.to_dict(orient='records'):
                perk_temp = {'rune'+str(rc)+'_'+k if k!='value' else 'rune'+str(rc):v for (k, v) in row2.items()}
                perks_temp.update(perk_temp)
                rc += 1

            runes_temp = pd.DataFrame(perks_temp, index=[0])
            runes_temp.insert(0, 'live_data_match_urn', self.match_id)
            runes_temp.insert(1, 'live_data_player_urn', row['liveDataPlayerUrn'])
            runes = pd.concat([runes, runes_temp])
        
        return runes
