import mwclient
import pandas as pd
import json

class PlayerLeaguepedia:
    def __init__(self,startdate,enddate):
        self.startdate = startdate
        self.enddate = enddate
        self.site = mwclient.Site('lol.fandom.com', path='/')
  
    def players(self,teamName):
        players = []
        response = self.site.api('cargoquery',
            limit = "max",
            tables = "ScoreboardGames=SG, ScoreboardPlayers=SP ",
            join_on = "SG.GameId=SP.GameId",
            fields = "SP.Name",
            where = 'SG.DateTime_UTC <= "%s" AND SG.DateTime_UTC>= "%s" AND SP.Team="%s"'%(self.enddate,self.startdate,teamName),
            group_by="SP.Name"
        )
        xd = json.dumps(response)
        xd2 = json.loads(xd)

        for x in xd2['cargoquery']:
                players.append((x['title']['Name']))
        return players
        
    def player_stats(self,players):
        champions = []
        for p in players:
                response2 = self.site.api('cargoquery',
                    limit = "max",
                    tables = "ScoreboardGames=SG, ScoreboardPlayers=SP",
                    join_on = "SG.GameId=SP.GameId",
                    fields = "SP.Champion,SP.PlayerWin,SP.Name,SG.Patch,SG.DateTime_UTC",
                    where = "SG.DateTime_UTC <= '%s' AND SG.DateTime_UTC>= '%s' AND SP.Name='%s'"%(self.enddate,self.startdate,p),
                    )
                xd3 = json.dumps(response2)
                xd4 = json.loads(xd3)
                for q in xd4['cargoquery']:
                    if q['title']['PlayerWin'] == 'Yes':
                        patchstr = q['title']['Patch']
                        if int(q['title']['Patch'].split(".")[1])<10:
                            patchstr = q['title']['Patch'].split(".")[0] + ".0" + q['title']['Patch'].split(".")[1]
                        champions.append([q['title']['Champion'],'1',q['title']['Name'],patchstr,q['title']['DateTime UTC']])
                    else:
                        patchstr = q['title']['Patch']
                        if int(q['title']['Patch'].split(".")[1])<10:
                            patchstr = q['title']['Patch'].split(".")[0] + ".0" + q['title']['Patch'].split(".")[1]
                        champions.append([q['title']['Champion'],'0',q['title']['Name'],patchstr,q['title']['DateTime UTC']])
        df = pd.DataFrame(champions,columns=['champion','result','player','patch','DateTime UTC'])
        df.sort_values(by=['DateTime UTC'],inplace=True)
        df['patch'] = df['patch'].astype(float)

        return df.sort_values(by=['patch'], ascending=False)
