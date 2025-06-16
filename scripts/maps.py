import json
import urllib
import os
import sys
import pandas as pd
import numpy as np
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from config import *
from multiprocessing.pool import ThreadPool
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from datetime import timedelta


class Maps:
    def __init__(self) -> None:
        self.abs_path = os.path.dirname(os.path.abspath(__file__))
        self.champ_img_path = self.abs_path+"/championImages/"

    def check_patch(self):
        patches_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        with urllib.request.urlopen(patches_url) as url:
            patches = json.loads(url.read().decode())
        last_patch = patches[0]
        return last_patch

    def download_champion_images(self, last_patch):
        champions_url = 'http://ddragon.leagueoflegends.com/cdn/' + \
            last_patch+'/data/en_US/champion.json'
        champion_images_dict = {'championName': [
            "Patch"], 'championPath': [last_patch]}
        champion_images_df = pd.DataFrame(champion_images_dict, index=[0])

        with urllib.request.urlopen(champions_url) as url:
            champions = json.loads(url.read().decode())
        for champion in champions['data']:
            champion_id = str(champions['data'][champion]['id'])
            champion_image_url = 'http://ddragon.leagueoflegends.com/cdn/%s/img/champion/%s.png' % (
                last_patch, champion_id)
            champion_image_name = str(champions['data'][champion]['image']['full'])
            urllib.request.urlretrieve(champion_image_url, self.champ_img_path + 
                                                            champion_image_name)
            
            champion_row_df = pd.DataFrame({'championName': champions['data'][champion]['name'], 
                                            'championPath': champion_image_name}, index=[0])
            champion_images_df = pd.concat([champion_images_df, champion_row_df], 
                                           ignore_index=True)

        champion_images_df.to_csv(self.champ_img_path+'champion_images_df.csv', index=False)

    def get_champ_file_name(self, champion_name):
        patches_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        with urllib.request.urlopen(patches_url) as url:
            patches = json.loads(url.read().decode())
        last_patch = patches[0]

        champions_url = 'http://ddragon.leagueoflegends.com/cdn/' + \
            last_patch+'/data/en_US/champion.json'
        with urllib.request.urlopen(champions_url) as url:
            champions = json.loads(url.read().decode())
        for champion in champions['data']:
            if str(champions['data'][champion]['name']) == champion_name:
                champion_file_name = str(
                    champions['data'][champion]['image']['full'])
        return champion_file_name

    def create_maps(self, event_positions_df):
        try:
            champion_images_df = pd.read_csv(self.champ_img_path+'champion_images_df.csv')
            df_patch = champion_images_df['championPath'].iloc[0]
            if (p := self.check_patch()) != df_patch:
                self.download_champion_images(p)
        except:
            self.download_champion_images(self.check_patch())
            champion_images_df = pd.read_csv(self.champ_img_path+'champion_images_df.csv')


        mask_im = Image.open(self.abs_path+'/masks/mask_circle.png').convert('L').resize((30, 30))
        mask_blur = Image.open(self.abs_path+'/masks/transparent_mask.png').convert('L').resize((92, 92))
        font = ImageFont.truetype(self.abs_path+"/masks/Inconsolata-SemiBold.ttf", 14)
        fog = Image.new('RGB', (92, 92), color='white')

        games = event_positions_df.live_data_match_urn.unique()
        event_positions_df = event_positions_df[(event_positions_df['live_data_match_urn'].isin(games))]
        maps_df = pd.DataFrame()

        for game in games:
            killer_team_side = None
            events = event_positions_df[(event_positions_df['live_data_match_urn'] == game)]['objective_id'].unique()
            map_paths = []
            image_names = []

            for event in events:
                timers = event_positions_df[(event_positions_df['live_data_match_urn'] == game) & 
                                            (event_positions_df['objective_id'] == event)]['time'].unique()

                for timer in timers:
                    # creating df for this timer
                    temp_df = event_positions_df[(event_positions_df['time'] == timer) &
                                                  (event_positions_df['live_data_match_urn'] == game)]
                    rift = Image.open(self.abs_path+"/masks/srx.png").resize((512, 512))
                    enhancer = ImageEnhance.Brightness(rift)

                    # creating range indicators for alive champs
                    for row in temp_df.to_dict(orient='records'):
                        if row['alive'] == True and row['objective_name'] == 'lvl1':
                            fog = Image.new('RGB', (92, 92), color=row['side'])
                            rift.paste(fog, (int((float(row['player_location_x'])*512/14990)-54),
                                             int((512 - float(row['player_location_y'])*512/15100))-54), mask_blur)

                    # iterating over this seconds df 
                    for row in temp_df.to_dict(orient='records'):
                        champion_image_name = champion_images_df.loc[champion_images_df['championName']
                                                                     == row['champion_name'], 'championPath'].iloc[0]
                        icon = Image.open(self.champ_img_path +
                                          champion_image_name).resize((30, 30))

                        if row['alive'] == False:
                            icon = icon.convert('L').convert('RGB')
                        draw_icon = ImageDraw.Draw(icon)
                        draw_icon.ellipse((0, 0)+(30, 30), outline=row['side'], width=3)

                        if row['alive'] == False:
                            enhancer = ImageEnhance.Brightness(icon)
                            icon = enhancer.enhance(0.5)
                        rift.paste(icon, (int((float(row['player_location_x'])*512/14990)-24),
                                          int((512 - float(row['player_location_y'])*512/15100))-24), mask_im)

                        if row['live_data_team_urn'] == row['killer_team_urn'] and row['objective_name'] != 'lvl1':
                            killer_team_side = row['side']

                    game_time = '_'.join(str(timedelta(milliseconds=row['time'])).split(':')[-2:]).split('.')[0]
                    draw_rift = ImageDraw.Draw(rift, 'RGBA')
                    if row['objective_name'] == 'lvl1':
                        draw_rift.text((0, 0), row['objective_id'] + ' ' + '_' + game_time,
                           (255, 255, 255), font=font)
                    else:
                        draw_rift.text((0, 0), row['objective_id'] + ' ' + game_time, (255, 255, 255), font=font)

                    image_name = row['live_data_match_urn'].split(':')[-1] + '_' + game_time +'.jpg'
                    image_path = (self.abs_path+'/temp/maps/' + image_name)
                    folder_image_name = (row['live_data_match_urn'].split(':')[-1]).upper() + '/' + image_name
                    map_paths.append(image_path)
                    image_names.append(folder_image_name)
                    rift.convert('RGB').save(image_path)

                try:
                    temp_map_df = pd.DataFrame({'live_data_match_urn': row['live_data_match_urn'], 
                            'objective_id': row['live_data_match_urn'] + '_' + row['objective_id'],
                            'time': row['time'], 'map_1': map_paths[0], 'map_2': map_paths[1], 'map_3': map_paths[2],
                            'name_1': image_names[0], 'name_2': image_names[1], 'name_3': image_names[2],
                            'objective_name': row['objective_name'], 'killer_team_side': killer_team_side, 
                            'blue_gold_spent': row['blue_gold_spent'], 'red_gold_spent': row['red_gold_spent'], 
                            'blue_team_name': row['blue_team_name'], 'red_team_name': row['red_team_name'], 
                            'objective_type': row['objective_type']}, index=[0])
                except:
                    temp_map_df = pd.DataFrame()
                maps_df = pd.concat([maps_df, temp_map_df])
                map_paths= []
                image_names = []

        return maps_df.reset_index(drop=True)


    def send_maps(self, event_positions_df, game_type):
        start = time.time()
        self.maps_df = self.create_maps(event_positions_df)
        end = time.time()
        print("tworzenie mapek: ")
        print(end-start)

        filenames = self.maps_df['map_1'].values.tolist()
        filenames.extend(self.maps_df['map_2'].values.tolist())
        filenames.extend(self.maps_df['map_3'].values.tolist())

        def upload(myfile):
            key = str(game_type) + '/' + (myfile.split('/')[-1]).upper().split('_')[0] + '/' + myfile.split('/')[-1]
            s3.upload_file(myfile, bucket, key)

        start = time.time()
        pool = ThreadPool(processes=8)
        pool.map(upload, filenames)
        

        for row in self.maps_df.to_dict(orient='records'):
            for x in range(1,4):
                object_url = "https://eu2.contabostorage.com/{0}:{1}/{2}".format(
                    storage_url, 
                    bucket, 
                    str(game_type) + '/' + str(row['name_'+str(x)])
                )
                self.maps_df = self.maps_df.replace([row['map_'+str(x)]], object_url)

        end = time.time()
        print("wysyłanie mapek: ")
        print(end-start)

        # remove files from dir
        for file in os.scandir(self.abs_path+'/temp/maps/'):
            os.remove(file.path)

        return self.maps_df
