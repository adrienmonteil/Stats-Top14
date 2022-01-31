# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 18:12:56 2021

@author: monte
"""


# import libraries
import pandas as pd
import numpy as np

import time
from bs4 import BeautifulSoup
import urllib.request
from selenium import webdriver
import re
import pygame

#import winsound

###############################################################################
# =============================================================================
#                               Automatisation                                #
# =============================================================================
###############################################################################

###############################################################################
#                             WEBSITE CONNEXION                               #
###############################################################################

def set_driver(url, button_cookies) :
    driver = webdriver.Chrome("C:/Users/monte/Downloads/chromedriver.exe")
    driver.get(url)
    time.sleep(6)
    #soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.find_element_by_xpath("//button[. = '" + str(button_cookies) + "']").click()            #Accept cookies
    time.sleep(5)
    return driver


def prepare_soup(driver, tab) :
    driver.find_element_by_xpath("//span[. = '" + str(tab) + "']").click()      #Click on the tab we need
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup



###############################################################################
#                                 EVENT DATA                                  #
###############################################################################

def load_match_data (url, game_day) :
    url = url.replace('match', 'commentary')
    
    # query the website and return the html to the variable 'page'
    page = urllib.request.urlopen(url)
    
    # parse the html using beautiful soup and store in variable 'soup'
    soup = BeautifulSoup(page, 'html.parser')
        
    # find events within table
    table = soup.find('div', attrs={'class': 'content match-commentary__content'})
    results = table.find_all('tr')
    
    col_min, col_home_score, col_away_score, col_action, col_player, col_team = [], [], [], [], [], []
    for i in results[::-1] :
        if len(i.find_all('td')[1]['class']) == 2 :
            col_min.append(float(i.getText().split('\'')[0]))
            col_home_score.append(col_home_score[-1])
            col_away_score.append(col_away_score[-1])
            col_action.append('Drop Goal Missed')
            col_player.append('')
            col_team.append('')
            
        elif i.find_all('td')[1]['class'][2] == 'icon-soccer-substitution-before' :
            if '+' in i.getText() :
                col_min.append(sum([int(i) for i in re.findall('\d+', i.getText() )]))
            else : col_min.append(float(i.getText().split('\'')[0]))
            col_home_score.append(col_home_score[-1])
            col_away_score.append(col_away_score[-1])
            #print(i.getText())
            if 'Substitute on' in i.getText() :
                col_action.append('Substitute on')
            elif 'Player substituted' in i.getText() :
                col_action.append('Substitute off')
            col_player.append(i.getText().split(' - ')[1].split(' , ')[0])
            col_team.append(i.getText().split(' - ')[1].split(' , ')[1])
            
        elif i.find_all('td')[1]['class'][2] == 'icon-soccer-foul-solid-before' :
            col_min.append(float(i.getText().split('\'')[0]))
            col_home_score.append(i.getText().split('\'')[1].split(' ')[0].split('-')[0])
            col_away_score.append(i.getText().split('\'')[1].split(' ')[0].split('-')[1])
            col_action.append((' ').join(i.getText().split('\'')[1].split(' ')[1:]))
            col_player.append('')
            col_team.append('')
            
        elif len(i.find_all('td')[1]['class']) == 4 :
            col_min.append(float(i.getText().split('\'')[0]))
            col_home_score.append(col_home_score[-1])
            col_away_score.append(col_away_score[-1])
            if 'yellow' in i.find_all('td')[1]['class'][3] :
                col_action.append('Yellow card')
            if 'red' in i.find_all('td')[1]['class'][3] :
                col_action.append('Red card')
            # a = (' ').join(i.getText().split('\'')[1].split(' ')[3:])
            #col_player.append(a.split(' , ')[0])
            #col_team.append(a.split(' , ')[1])
            col_player.append(i.getText().split(' - ')[1].split(' , ')[0])
            col_team.append(i.getText().split(' - ')[1].split(' , ')[1])
            
        else :
            col_min.append(float(i.getText().split('\'')[0]))
            col_home_score.append(i.getText().split('\'')[1].split(' ')[0].split('-')[0])
            col_away_score.append(i.getText().split('\'')[1].split(' ')[0].split('-')[1])
            a = (' ').join(i.getText().split('\'')[1].split(' ')[1:])
            col_action.append(a.split(' - ')[0])
            if a == 'Penalty try' :
                col_player.append('')
                col_team.append('')
            else :
                col_player.append(i.getText().split(' - ')[1].split(' , ')[0])
                col_team.append(i.getText().split(' - ')[1].split(' , ')[1])
    m_id = 'FR' + url[-6:] + url[45:51]
    match_id = [m_id for i in range(len(col_min))]
    game_day = [game_day for i in range(len(col_min))]
    d1 = {'GAME_DAY' : game_day, 'MATCH_ID' : match_id, 'MINUTE' : col_min, 'HOME_SCORE' : col_home_score, 'AWAY_SCORE' : col_away_score,
         'ACTION_TYPE' : col_action, 'PLAYER' : col_player, 'TEAM' : col_team}
    #print(d1)
    data = pd.DataFrame(data=d1)

    if len(data.loc[data.HOME_SCORE.str.contains('\+'), 'MINUTE']) != 0 :
        data.loc[data.HOME_SCORE.str.contains('\+'), 'MINUTE'] += float(data.loc[data.HOME_SCORE.str.contains('\+'),'HOME_SCORE'].values[0][1])
        data.loc[data.HOME_SCORE.str.contains('\+'), 'HOME_SCORE'] = data.loc[data.HOME_SCORE.str.contains('\+'),'HOME_SCORE'].values[0][2:]
    data.HOME_SCORE = pd.to_numeric(data.HOME_SCORE)
    data.AWAY_SCORE = pd.to_numeric(data.AWAY_SCORE)
    data.MATCH_ID = data.MATCH_ID.astype(str)
    
    
    # find home and away team
    header = soup.find('div', attrs={'class': 'competitors'})
    home_score = int(header.find('div', attrs={'class': 'team team-a'}).find('div', attrs={'class': 'team__content'}).find('div', attrs={'class': 'score-container'}).getText())
    away_score = int(header.find('div', attrs={'class': 'team team-b'}).find('div', attrs={'class': 'team__content'}).find('div', attrs={'class': 'score-container'}).getText())
    home_team = header.find('div', attrs={'class': 'team team-a'}).find_all('span')[1].getText()
    away_team = header.find('div', attrs={'class': 'team team-b'}).find_all('span')[1].getText()
    
    d2 = {'MATCH_ID' : m_id, 'SAISON_ID' : ['20202021'], 'COMPETITION_ID' : [url[-6:]]
          , 'HOME_TEAM' : [home_team], 'AWAY_TEAM' : [away_team]
          , 'HOME_SCORE' : [home_score], 'AWAY_SCORE' : [away_score]}
    data_info = pd.DataFrame(data=d2)
    
    return data, data_info



###############################################################################
#                              PLAYER STATS DATA                              #
###############################################################################

def get_name(url) :
    try :
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page, 'html.parser')
        
        name = soup.find('div', attrs={'class': 'scrumPlayerDesc'})
        return name.text.replace('Full name ', '')
    except :
        return url


def create_stat_dataframe(h, d, n, url, team) :
    stats = {}
    
    m_id = 'FR' + url[-6:] + url[46:52]
    stats['MATCH_ID'] = [m_id for i in range(int(len(d)/len(h)))]
    stats['TEAM'] = [team for i in range(int(len(d)/len(h)))]
    stats['PLAYER'] = [get_name(n[i]['href']) for i in range (len(n))]
    for col_num in range(1,len(h)) :
        stats[h[col_num].text] = [d[i+col_num].getText() for i in [i*len(h) for i in range(int(len(d)/len(h)))]]
    data = pd.DataFrame(data=stats)
    return data



def load_player_stats(url, tab, driver) :
    soup = prepare_soup(driver, tab)  
 
    t1 = soup.find('div', attrs={'class' : 'sub-module tabbedTable'})
    t2 = t1.find('div', attrs={'class' : 'tab-content'})
    
    header = soup.find('div', attrs={'class': 'competitors'})
    team1 = header.find('div', attrs={'class': 'team team-a'}).find_all('span')[1].getText()
    team2 = header.find('div', attrs={'class': 'team team-b'}).find_all('span')[1].getText()

    #for home team
    h1 = t2.select('[class="table-wrap active"] th') #select the header
    d1 = t2.select('[class="table-wrap active"] td') #select the data
    n1 = t2.select('[class="table-wrap active"] a')
    #for away team
    h2 = t2.select('[class="table-wrap"] th') #select the header
    d2 = t2.select('[class="table-wrap"] td') #select the data
    n2 = t2.select('[class="table-wrap"] a')
    
    data = pd.concat([create_stat_dataframe(h1,d1,n1,url,team1), create_stat_dataframe(h2,d2,n2,url,team2)], ignore_index = True)
    return data
 


def concat_tabs(url, driver) :
    scoring = load_player_stats(url, 'Scoring', driver)
    attacking = load_player_stats(url, 'Attacking', driver)
    defending = load_player_stats(url, 'Defending', driver)
    discipline = load_player_stats(url, 'Discipline', driver)
    data = pd.concat([scoring, attacking, defending, discipline], axis = 1)
    data = data.drop('-', axis=1)
    return data.loc[:,~data.columns.duplicated()]



###############################################################################
#                               TEAM STATS DATA                               #
###############################################################################

def load_team_stats(url) :
    url = url.replace('match', 'matchstats')
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    
    #get data from 'Attacking' part of Match Stats report
    table_attacking = soup.find('article', attrs={'class': 'sub-module', 'style' : 'overflow:auto;'})
    s = table_attacking.find_all('tr')
    
    #get data from 'Set pieces' part of Match Stats report
    set_pieces = soup.find_all('div', attrs={'class': 'sub-module-split'})[1].find_all('div', attrs={'class': 'countLabel'})
    
    #get team names
    t1 = soup.find('div', attrs={'class' : 'competitors'})
    t2 = t1.find_all('span', attrs={'class' : 'long-name'})
    home_team = t2[0].text
    away_team = t2[1].text
    
    #create DataFrame
    stats = {}
    m_id = 'FR' + url[-6:] + url[45:51]
    stats[home_team] = [m_id
                        , float(s[0].text.split('%')[0]), float(s[0].text.split('%')[1].split(' / ')[1])    #possession 1st and 2nd half
                        , float(s[1].text.split('%')[0]), float(s[1].text.split('%')[1].split(' / ')[1])  #territory 1st and 2nd half
                        , int(s[2].text.split('Clean Breaks')[0])  #Clean breaks
                        , int(s[3].text.split('Defenders Beaten')[0])  #Defenders beaten
                        , int(s[4].text.split('Offload')[0])  #Offloads
                        , int(s[5].text.split(' / ')[0])   #Ruck won
                        , float(s[5].text.split('(')[1].split('%')[0])   #Ruck won (%)
                        , int(s[6].text.split('/')[0]) #Maul won
                        , float(s[6].text[s[6].text.index('(')+1 : s[6].text.index('%')])  #Maul won (%)
                        , int(s[7].text.split('Turnovers Conceded')[0]) #Turnovers conceded
                        , int(set_pieces[0].text.split('/')[0])    #Scrum won
                        , float(set_pieces[0].text.split('/')[1].split(' ')[1].split('%')[0][1:])  #Scrum won (%)
                        , int(set_pieces[2].text.split('/')[0])    #Lineout won
                        , float(set_pieces[2].text.split('/')[1].split(' ')[1].split('%')[0][1:]) ]    #Lineout won (%)
    
    stats[away_team] = [m_id
                        , float(s[0].text.split('2H')[1].split('%')[0]), float(s[0].text.split('2H')[1].split('%')[1].split(' / ')[1])
                        , float(s[1].text.split('2H')[1].split('%')[0]), float(s[1].text.split('2H')[1].split('%')[1].split(' / ')[1])
                        , int(s[2].text.split('Clean Breaks')[1])
                        , int(s[3].text.split('Defenders Beaten')[1])
                        , int(s[4].text.split('Offload')[1])
                        , int(s[5].text.split('Rucks Won')[1].split('/')[0])
                        , float(s[5].text.split(' ')[-1].split('%')[0][1:])
                        , int(s[6].text.split('Mauls Won')[1].split(' /')[0])
                        , float(s[6].text.split(' ')[-1].split('%')[0][1:])
                        , int(s[7].text.split('Turnovers Conceded')[1])
                        , int(set_pieces[1].text.split('/')[0])
                        , float(set_pieces[1].text.split('/')[1].split(' ')[1].split('%')[0][1:])
                        , int(set_pieces[3].text.split('/')[0])
                        , float(set_pieces[3].text.split('/')[1].split(' ')[1].split('%')[0][1:]) ]
    
    colnames = ['MATCH_ID', 'POSSESSION_1H', 'POSSESSION_2H', 'TERRITORY_1H', 'TERRITORY_2H'
                , 'CLEAN_BREAKS', 'DEFENDERS_BEATEN', 'OFFLOAD', 'RUCK_WON_NB', 'RUCK_WON_PCT'
                , 'MAUL_WON_NB', 'MAUL_WON_PCT', 'TURNOVERS_CONDEDED', 'SCRUM_WON_NB', 'SCRUM_WON_PCT'
                , 'LINEOUT_WON_NB', 'LINEOUT_WON_PCT']
    data = pd.DataFrame.from_dict(data=stats, orient='index', columns=colnames)
    data.index = data.index.set_names(['TEAM'])
    colnames = [colnames[0]] + ['TEAM'] + colnames[1:]
    return data.reset_index()[colnames]


def load_all_matches(url_list, game_day) :
    matches_event, matches_info = load_match_data(url_list[0], game_day)
    driver = set_driver(url_list[0].replace('match', 'playerstats'), 'I Accept')
    players_stats = concat_tabs(url_list[0].replace('match', 'playerstats'), driver)
    team_stats = load_team_stats(url_list[0])
    driver.quit()
    i=1
    print ('Match : ' + str(i))
    for url in url_list[1:] :
        i+=1
        data_event, data_info = load_match_data(url, game_day)
        data_team = load_team_stats(url)
        driver = set_driver(url.replace('match', 'playerstats'), 'I Accept')
        data_stats = concat_tabs(url.replace('match', 'playerstats'), driver)
        driver.quit()
        
        matches_event = pd.concat([matches_event, data_event], ignore_index=True)
        matches_info = pd.concat([matches_info, data_info], ignore_index=True)
        players_stats = pd.concat([players_stats, data_stats], ignore_index=True)
        team_stats = pd.concat([team_stats, data_team], ignore_index=True)
        
        print('Match : ' + str(i))
        
        time.sleep(np.random.randint(low = 3, high = 10))
    
    return matches_event, matches_info, players_stats, team_stats

def update(path, new_df) :
    old_df = pd.read_csv(path, sep=';')
    old_df = pd.concat([new_df, old_df], ignore_index=True)
    old_df.to_csv(path, sep=';', index=False)
   
def data_to_csv(L, game_day) :
    start_time = time.time()
    assert len(L) == len(set(L)), "Match links are not all differents"
    events, info, pl_stats, tm_stats = load_all_matches(L, game_day)
    update('D:/Documents/Stats/Rugby/web_scrapping/data_event.csv', events)
    update('D:/Documents/Stats/Rugby/web_scrapping/data_info.csv', info)
    update('D:/Documents/Stats/Rugby/web_scrapping/player_stats.csv', pl_stats)
    update('D:/Documents/Stats/Rugby/web_scrapping/team_stats.csv', tm_stats)  

    duree = time.time() - start_time
    print('Durée du programme : ' + str(int(duree/60)) + 'min ' +str(int(duree/60%1*60)) + 's')
    
    # duration = 800  # milliseconds
    # freq = 800  # Hz
    # winsound.Beep(freq, duration)
    # winsound.Beep(freq, duration)
    # winsound.Beep(freq, duration)
    # winsound.Beep(freq, duration)
    # winsound.Beep(1200, duration)
    pygame.mixer.init()
    pygame.mixer.music.load('D:\Documents\Stats\Rugby\web_scrapping\Sons\son_brahimi.mp3')
    pygame.mixer.music.play()

###############################################################################
# =============================================================================
# Run this code
# =============================================================================
###############################################################################  

# M1 = ''
# M2 = ''
# M3 = ''
# M4 = ''
# M5 = ''
# M6 = ''
# M7 = ''

M1 = 'https://www.espn.com/rugby/match?gameId=593405&league=270559'
M2 = 'https://www.espn.com/rugby/match?gameId=593406&league=270559'
M3 = 'https://www.espn.com/rugby/match?gameId=593407&league=270559'
M4 = 'https://www.espn.com/rugby/match?gameId=593408&league=270559'
M5 = 'https://www.espn.com/rugby/match?gameId=593409&league=270559'
M6 = 'https://www.espn.com/rugby/match?gameId=593410&league=270559'
M7 = 'https://www.espn.com/rugby/match?gameId=593411&league=270559'
L = [M1, M2, M3, M4, M5, M6, M7]

data_to_csv(L, 26)
