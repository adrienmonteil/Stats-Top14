



import pandas as pd
import numpy as np


####################################
## Take into acount penalty tries ##
####################################

# Assign a team to each penalty try
df_event=pd.read_csv('./2. Exports/data_event.csv', sep=';')
df_info=pd.read_csv('./2. Exports/data_info.csv', sep=';')[['MATCH_ID','HOME_TEAM','AWAY_TEAM']]
df_event = df_event.join(df_info.set_index('MATCH_ID'), on='MATCH_ID')

df_event.loc[df_event['TEAM']=='HOME_TEAM', "TEAM"] = df_event.loc[df_event['TEAM']=='HOME_TEAM', "HOME_TEAM"]
df_event.loc[df_event['TEAM']=='AWAY_TEAM', "TEAM"] = df_event.loc[df_event['TEAM']=='AWAY_TEAM', "AWAY_TEAM"]

df_event = df_event.drop(['HOME_TEAM', 'AWAY_TEAM'], axis=1)

#Get all penalty tries

df_pen_tries = pd.DataFrame(df_event.loc[df_event.ACTION_TYPE=='Penalty try', :].groupby(by=['MATCH_ID','TEAM']).count()['MINUTE']).rename(columns={'MINUTE' : 'Penalty_try'})

df_pen_tries.shape
#Add more infos

df_player=pd.read_csv('./2. Exports/player_stats.csv', sep=';')
df_player_group = df_player.groupby(by=['MATCH_ID','TEAM']).sum()[['T','TA','CG','PG','DGC','PTS','P','R','MR','Tackles','MT','PC','YC','RC']]
df_player_group = df_player_group.rename(columns={'T' : 'Try'
                        ,'TA' : 'Assist'
                        ,'CG' : 'Conversion'
                        ,'PG' : 'Penalty_goal'
                        ,'DGC' : 'Drop_goal'
                        ,'PTS' : 'Score_for'
                        ,'P' : 'Passes'
                        ,'R' : 'Run'
                        ,'MR' : 'Meters_run'
                        ,'MT' : 'Missed_tackles'
                        ,'PC' : 'Penalties_conceded'
                        ,'YC' : 'Yellow_cards'
                        ,'RC' :  'Red_cards'})
# df_player_group.to_csv('./2. Exports/test.csv', sep=';', index=False)
df_player_group = df_player_group.join(df_pen_tries, on=['MATCH_ID', 'TEAM'])
df_player_group['Penalty_try'] = df_player_group['Penalty_try'].fillna(0)
df_player_group.Score_for = df_player_group.Score_for + 7*df_player_group.Penalty_try
df_temp = df_player_group.groupby(by='MATCH_ID').sum()[['Score_for','Try','Penalty_try']].rename(columns={'Score_for' : 'tot_score', 'Try' : 'tot_try', 'Penalty_try' : 'tot_pen_try'})
df_player_group = df_player_group.join(df_temp, on='MATCH_ID')

df_player_group['Score_against'] = df_player_group['tot_score'] - df_player_group['Score_for']
df_player_group['Try_against'] = df_player_group['tot_try'] - df_player_group['Try']
df_player_group['Penalty_try_against'] = df_player_group['tot_pen_try'] - df_player_group['Penalty_try']

def game_result(s) :
    if s['Score_for'] > s['Score_against'] :
        return "W"
    elif s['Score_for'] == s['Score_against'] :
        return "D"
    elif s['Score_for'] < s['Score_against'] :
        return "L"

df_player_group['Result'] = df_player_group.apply(game_result, axis=1)


def bonus(s) :
    bonus=0
    if s['Try']+s['Penalty_try'] >= s['Try_against']+s['Penalty_try_against']+3 :
        bonus += 1
    if s['Score_against'] > s['Score_for'] >= s['Score_against']-5 :
        bonus += 1
    return bonus

df_player_group['Bonus_point'] = df_player_group.apply(bonus, axis=1)

def game_points(s) :
    if s['Result'] == "W" :
        return 4 + s['Bonus_point']
    elif s['Result'] == "L" :
        return 0 + s['Bonus_point']
    elif s['Result'] == "D" :
        return 2 + s['Bonus_point']

df_player_group['Match_points'] = df_player_group.apply(game_points, axis=1)



df_player_group = df_player_group.drop(['tot_score', 'tot_try', 'tot_pen_try'], axis=1)

df_team=pd.read_csv('./2. Exports/team_stats.csv', sep=';')
df = df_team.join(df_player_group, on=['MATCH_ID', 'TEAM'])

df.to_csv('./2. Exports/team_stats_full.csv', sep=';', index=False)