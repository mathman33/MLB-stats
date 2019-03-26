import urllib2
from bs4 import BeautifulSoup
import re

teamstamp = {
    # National League
        # West
    "Los Angeles Dodgers": "LAD",
    "Arizona Diamondbacks": "ARI",
    "San Francisco Giants": "SFG",
    "Colorado Rockies": "COL",
    "San Diego Padres": "SDP",
        # Central
    "Chicago Cubs": "CHC",
    "St. Louis Cardinals": "STL",
    "Cincinnati Reds": "CIN",
    "Pittsburgh Pirates": "PIT",
    "Milwaukee Brewers": "MIL",
        # East
    "Miami Marlins": "FLA",
    "New York Mets": "NYM",
    "Washington Nationals": "WSN",
    "Atlanta Braves": "ATL",
    "Philadelphia Phillies": "PHI",

    # American League
        # West
    "Los Angeles Angels": "ANA",
    "Oakland Athletics": "OAK",
    "Texas Rangers": "TEX",
    "Seattle Mariners": "SEA",
    "Houston Astros": "HOU",

        # Central
    "Chicago White Sox": "CHW",
    "Cleveland Indians": "CLE",
    "Detroit Tigers": "DET",
    "Kansas City Royals": "KCR",
    "Minnesota Twins": "MIN",

        # East
    "Boston Red Sox": "BOS",
    "Baltimore Orioles": "BAL",
    "Tampa Bay Rays": "TBD",
    "New York Yankees": "NYY",
    "Toronto Blue Jays": "TOR"
}

def scrape_box_data(linescore):
    box_data = {"away":{},"home":{}}

    teams_soup = linescore.find('tbody')
    teams_list = teams_soup.find_all('tr')

    away_team_box = teams_list[0].find_all('td')
    box_data["away"]["team_name"] = away_team_box[1].get_text()
    away_team_innings = []
    for i in xrange(2,len(away_team_box)-3):
        away_team_innings.append(away_team_box[i].get_text())
    box_data["away"]["innings"] = away_team_innings
    box_data["away"]["runs"] = int(away_team_box[-3].get_text())
    box_data["away"]["hits"] = int(away_team_box[-2].get_text())
    box_data["away"]["errors"] = int(away_team_box[-1].get_text())

    home_team_box = teams_list[1].find_all('td')
    box_data["home"]["team_name"] = home_team_box[1].get_text()
    home_team_innings = []
    for i in xrange(2,len(home_team_box)-3):
        home_team_innings.append(home_team_box[i].get_text())
    box_data["home"]["innings"] = home_team_innings
    box_data["home"]["runs"] = int(home_team_box[-3].get_text())
    box_data["home"]["hits"] = int(home_team_box[-2].get_text())
    box_data["home"]["errors"] = int(home_team_box[-1].get_text())

    box_data["winning_team"] = box_data["away"]["team_name"] if box_data["away"]["runs"] > box_data["home"]["runs"] else box_data["home"]["team_name"]
    box_data["losing_team"] = box_data["away"]["team_name"] if box_data["away"]["runs"] < box_data["home"]["runs"] else box_data["home"]["team_name"]

    print "winner: ", box_data["winning_team"]
    print "loser: ", box_data["losing_team"]

    bottom_text_soup = linescore.find('tfoot')
    bottom_text_list = bottom_text_soup.find_all('tr')
    t = bottom_text_list[0].get_text()
    print t
    m = re.search(r'(?<=WP:.)(.*)(?=.\(.-.\).)', t)
    box_data["winning_pitcher"] = m.group().replace(u'\xa0', u' ')
    m = re.search(r'(?<=LP:.)(.*)(?=.\()', t)
    box_data["losing_pitcher"] = m.group().replace(u'\xa0', u' ')
    if len(bottom_text_list) > 1:
        box_data["extra_text"] = bottom_text_list[1].get_text()
    else:
        box_data["extra_text"] = ""

    return box_data

def scrape_game_data(game_link):
    soup = BeautifulSoup(urllib2.urlopen(game_link), 'html.parser')
    linescore = soup.find("div", attrs={"class": "linescore_wrap"})
    box_data = scrape_box_data(linescore)

    away_team_name = box_data["away"]["team_name"]
    home_team_name = box_data["home"]["team_name"]



    batting_and_plays = soup.find_all("div", attrs={"class","table_wrapper"})
    away_batting = batting_and_plays[0]
    home_batting = batting_and_plays[1]
    top_5_plays = batting_and_plays[2]
    play_by_play = batting_and_plays[3]

    # section_wrappers = soup.find_all("div", attrs={"class","section_wrapper"})
    # other_games = section_wrappers[0]
    # pitching = section_wrappers[1]
    # other_info = section_wrappers[2]
    # win_probability_chart = section_wrappers[3]
    # play_by_play_explanation = section_wrappers[4]
    # pitching_content = pitching.find("div", attrs={"class", "table_outer_container"})

# box scores page from baseball-reference.com
BOX_SCORES_PAGE = "https://www.baseball-reference.com/boxes"

# test date and test page
date = "/?month=7&day=24&year=2018"
page = BOX_SCORES_PAGE+date

# get the html using BeautifulSoup
soup = BeautifulSoup(urllib2.urlopen(page), "html.parser")

# get a list of links of stats from each game
game_links = []
game_summary_list = soup.find_all('div', attrs={'class': 'game_summary nohover'})
for game in game_summary_list:
    final_link = game.find('td', attrs={'class': 'right gamelink'})
    link = final_link.find('a').get('href')
    game_links.append(BOX_SCORES_PAGE+link[6:])

# scrape game data from each game
# game_link = game_links[10]
# scrape_game_data(game_link)
for game_link in game_links:
    scrape_game_data(game_link)
    # break



