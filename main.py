import urllib2
from bs4 import BeautifulSoup
import re
import time

team_to_league = {
    "Los Angeles Dodgers": "NL",
    "Arizona Diamondbacks": "NL",
    "San Francisco Giants": "NL",
    "Colorado Rockies": "NL",
    "San Diego Padres": "NL",
    "Chicago Cubs": "NL",
    "St. Louis Cardinals": "NL",
    "Cincinnati Reds": "NL",
    "Pittsburgh Pirates": "NL",
    "Milwaukee Brewers": "NL",
    "Miami Marlins": "NL",
    "New York Mets": "NL",
    "Washington Nationals": "NL",
    "Atlanta Braves": "NL",
    "Philadelphia Phillies": "NL",
    "Los Angeles Angels": "AL",
    "Oakland Athletics": "AL",
    "Texas Rangers": "AL",
    "Seattle Mariners": "AL",
    "Houston Astros": "AL",
    "Chicago White Sox": "AL",
    "Cleveland Indians": "AL",
    "Detroit Tigers": "AL",
    "Kansas City Royals": "AL",
    "Minnesota Twins": "AL",
    "Boston Red Sox": "AL",
    "Baltimore Orioles": "AL",
    "Tampa Bay Rays": "AL",
    "New York Yankees": "AL",
    "Toronto Blue Jays": "AL"
}

team_to_stamp = {
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

    bottom_text_soup = linescore.find('tfoot')
    bottom_text_list = bottom_text_soup.find_all('tr')
    t = bottom_text_list[0].get_text()
    m = re.search(r'(?<=WP:.)(.*)(?=.\(.{1,2}-.{1,2}\).)', t)
    box_data["winning_pitcher"] = m.group().replace(u'\xa0', u' ')
    m = re.search(r'(?<=LP:.)(.*)(?=.\()', t)
    box_data["losing_pitcher"] = m.group().replace(u'\xa0', u' ')
    if len(bottom_text_list) > 1:
        box_data["extra_text"] = bottom_text_list[1].get_text()
    else:
        box_data["extra_text"] = ""

    return box_data

def scrape_batting_data(batting_html):
    overthrow = batting_html.find("div", attrs={"class": "overthrow"})
    tbody = overthrow.find("tbody")
    rows = tbody.find_all("tr")

    batting_data = {}

    for row in rows:
        if not row.has_attr("class"):
            player_data = {}
            name_and_position = row.find("th").get_text()
            m = re.search(r"(.*) (.*)", name_and_position)
            player_name = m.group(1).replace(u'\xa0',u'')
            player_position = m.group(2)

            player_data["position"] = player_position

            batting_stats = row.find_all("td")
            player_data["AB"] = batting_stats[0].get_text()
            if player_data["AB"] != u'': player_data["AB"] = int(player_data["AB"])
            player_data["R"] = batting_stats[1].get_text()
            if player_data["R"] != u'': player_data["R"] = int(player_data["R"])
            player_data["H"] = batting_stats[2].get_text()
            if player_data["H"] != u'': player_data["H"] = int(player_data["H"])
            player_data["RBI"] = batting_stats[3].get_text()
            if player_data["RBI"] != u'': player_data["RBI"] = int(player_data["RBI"])
            player_data["BB"] = batting_stats[4].get_text()
            if player_data["BB"] != u'': player_data["BB"] = int(player_data["BB"])
            player_data["SO"] = batting_stats[5].get_text()
            if player_data["SO"] != u'': player_data["SO"] = int(player_data["SO"])
            player_data["PA"] = batting_stats[6].get_text()
            if player_data["PA"] != u'': player_data["PA"] = int(player_data["PA"])
            player_data["BA"] = batting_stats[7].get_text()
            if player_data["BA"] != u'': player_data["BA"] = float(player_data["BA"])
            player_data["OBP"] = batting_stats[8].get_text()
            if player_data["OBP"] != u'': player_data["OBP"] = float(player_data["OBP"])
            player_data["SLG"] = batting_stats[9].get_text()
            if player_data["SLG"] != u'': player_data["SLG"] = float(player_data["SLG"])
            player_data["OPS"] = batting_stats[10].get_text()
            if player_data["OPS"] != u'': player_data["OPS"] = float(player_data["OPS"])
            player_data["Pit"] = batting_stats[11].get_text()
            if player_data["Pit"] != u'': player_data["Pit"] = int(player_data["Pit"])
            player_data["Str"] = batting_stats[12].get_text()
            if player_data["Str"] != u'': player_data["Str"] = int(player_data["Str"])
            player_data["WPA"] = batting_stats[13].get_text()
            if player_data["WPA"] != u'': player_data["WPA"] = float(player_data["WPA"])
            player_data["aLI"] = batting_stats[14].get_text()
            if player_data["aLI"] != u'': player_data["aLI"] = float(player_data["aLI"])
            player_data["WPA+"] = batting_stats[15].get_text()
            if player_data["WPA+"] != u'': player_data["WPA+"] = float(player_data["WPA+"])
            player_data["WPA-"] = batting_stats[16].get_text()
            if player_data["WPA-"] != u'': player_data["WPA-"] = float(player_data["WPA-"])
            player_data["RE24"] = batting_stats[17].get_text()
            if player_data["RE24"] != u'': player_data["RE24"] = float(player_data["RE24"])
            player_data["PO"] = batting_stats[18].get_text()
            if player_data["PO"] != u'': player_data["PO"] = int(player_data["PO"])
            player_data["A"] = batting_stats[19].get_text()
            if player_data["A"] != u'': player_data["A"] = int(player_data["A"])
            player_data["Details"] = batting_stats[20].get_text()

            batting_data[player_name] = player_data
    return batting_data

def scrape_play_by_play_data(play_by_play_html, home_team_league):
    overthrow = play_by_play_html.find("div", attrs={"class": "overthrow"})
    tbody = overthrow.find("tbody")
    rows = tbody.find_all("tr")

    national_league_pitching_substitution_pattern = r"(.*?) replaces (.*?) pitching and batting (\d)(th|rd|st|nd)?"
    american_league_pitching_substitution_pattern = r"(.*?) replaces (.*?) pitching?"
    pinch_hitter_pattern = r"(.*?) pinch hits for (.*) \((.*)\) batting (\d)(th|rd|st|nd)?"
    pinch_runner_pattern = r"(.*?) pinch runs for (.*) \((.*)\) batting (\d)(th|rd|st|nd)?"
    fielding_substitution_pattern = r"(.*?) replaces (.*) \((.*)\) playing (.*) batting (\d)(th|rd|st|nd)?"
    move_pattern = r"(.*?) moves from (P|1B|2B|3B|SS|LF|RF|CF?|PH|DH?) to (P|1B|2B|3B|SS|LF|RF|CF?|PH|DH?)"
    if home_team_league == "NL":
        substitution_patterns = [national_league_pitching_substitution_pattern]
    elif home_team_league == "AL":
        substitution_patterns = [american_league_pitching_substitution_pattern]
    substitution_patterns.append(pinch_hitter_pattern)
    substitution_patterns.append(pinch_runner_pattern)
    substitution_patterns.append(fielding_substitution_pattern)
    substitution_patterns.append(move_pattern)

    play_by_play_data = []

    for row in rows:
        if row.has_attr('class'):
            if row['class'][0] == u'pbp_summary_top':
                half_inning_summary = row.get_text()
                m = re.search(r"(Top|Bottom) of the (.*), (.*) Batting, (Tied|Ahead|Behind) (.*)-(.*), (.*)' (.*) facing (\d-\d-\d)", half_inning_summary)
                top_or_bottom = m.group(1)
                inning = m.group(2)
                batting_team = m.group(3)
                batting_team_winning_losing = m.group(4)
                batting_team_score = m.group(5)
                pitching_team_score = m.group(6)
                pitching_team = m.group(7)
                pitcher = m.group(8)
                batting_order = m.group(9)

                pre_half_inning_summary = {
                    "top_or_bottom": top_or_bottom,
                    "inning": inning,
                    "batting_team": batting_team,
                    "batting_team_winning_losing": batting_team_winning_losing,
                    "batting_team_score": batting_team_score,
                    "pitching_team_score": pitching_team_score,
                    "pitching_team": pitching_team,
                    "pitcher": pitcher,
                    "batting_order": batting_order
                }
                play_by_play_data.append(("pre_half_inning_summary",pre_half_inning_summary))

            elif row['class'][0] == u'pbp_summary_bottom':
                half_inning_summary = row.get_text()
                m = re.search(r"(.*) runs?, (.*) hits?, (.*) errors?, (.*) LOB. (.*) (.*), (.*) (.*).", half_inning_summary)
                runs = int(m.group(1))
                hits = int(m.group(2))
                errors = int(m.group(3))
                LOB = int(m.group(4))
                away_team = m.group(5)
                away_team_score = int(m.group(6))
                home_team = m.group(7)
                home_team_score = int(m.group(8))

                post_half_inning_summary = {
                    "runs": runs,
                    "hits": hits,
                    "errors": errors,
                    "LOB": LOB,
                    "away_team": away_team,
                    "away_team_score": away_team_score,
                    "home_team": home_team,
                    "home_team_score": home_team_score
                }
                play_by_play_data.append(("post_half_inning_summary",post_half_inning_summary))

            elif u'top_inning' in row['class'][0] or u'bottom_inning' in row['class'][0]:
                columns = row.find_all('td')
                pre_AB_score = columns[0].get_text()
                m = re.search(r"(.*)-(.*)", pre_AB_score)
                pre_AB_batting_team_score = m.group(1)
                pre_AB_pitching_team_score = m.group(2)
                outs = columns[1].get_text()
                runners = columns[2].get_text()
                pitches = columns[3].get_text()
                m = re.search(r"(.*),\((.*)-(.*)\)",pitches)
                num_pitches = m.group(1)
                balls_at_event = m.group(2)
                strikes_at_event = m.group(3)
                runs_and_outs = columns[4].get_text()
                resulting_runs = int(runs_and_outs.count("R"))
                resulting_outs = int(runs_and_outs.count("O"))
                batting_teamstamp = columns[5].get_text()
                batter = columns[6].get_text()
                pitcher = columns[7].get_text()
                wWPA_text = columns[8].get_text()
                m = re.search(r"(.*)\%", wWPA_text)
                wWPA = int(m.group(1))
                wWE_text = columns[9].get_text()
                m = re.search(r"(.*)\%", wWE_text)
                wWE = int(m.group(1))
                description = columns[10].get_text()
                events = description.split('; ')
                score = u'bold' in row['class'][0]

                batter = {
                    "pre_AB_batting_team_score": pre_AB_batting_team_score,
                    "pre_AB_pitching_team_score": pre_AB_pitching_team_score,
                    "outs": outs,
                    "runners": runners,
                    "num_pitches": num_pitches,
                    "balls_at_event": balls_at_event,
                    "strikes_at_event": strikes_at_event,
                    "resulting_runs": resulting_runs,
                    "resulting_outs": resulting_outs,
                    "batting_teamstamp": batting_teamstamp,
                    "batter": batter,
                    "pitcher": pitcher,
                    "wWPA": wWPA,
                    "wWE": wWE,
                    "events": events,
                    "score": score
                }
                play_by_play_data.append(("batter",batter))
            
            elif row['class'][0] == u'ingame_substitution':
                columns = row.find_all("td")
                event = columns[8].get_text()
                num_subs = event.count("replaces") + event.count("moves") + event.count("pinch hits") + event.count("pinch runs")

                subs_list = []
                
                break_out = False
                while True:
                    if not break_out:
                        for i, pattern in enumerate(substitution_patterns):
                            m = re.search(pattern, event)
                            if m:
                                substitution = m.group()
                                substitution_data = {}
                                if i == 0:
                                    substitution_data["type"] = "pitching change"
                                    substitution_data["incoming_pitcher"] = str(m.group(1).replace(u'\xa0',u' '))
                                    substitution_data["outgoing_pitcher"] = str(m.group(2).replace(u'\xa0',u' '))
                                    if home_team_league == "NL":
                                        substitution_data["batting_order"] = int(m.group(3).replace(u'\xa0',u' '))
                                elif i == 1:
                                    substitution_data["type"] = "pinch hitter"
                                    substitution_data["pinch_hitter"] = str(m.group(1).replace(u'\xa0',u' '))
                                    substitution_data["outgoing_hitter"] = str(m.group(2).replace(u'\xa0',u' '))
                                    substitution_data["field_position"] = str(m.group(3).replace(u'\xa0',u' '))
                                    substitution_data["batting_order"] = int(m.group(4).replace(u'\xa0',u' '))
                                elif i == 2:
                                    substitution_data["type"] = "pinch runner"
                                    substitution_data["pinch_runner"] = str(m.group(1).replace(u'\xa0',u' '))
                                    substitution_data["outgoing_runner"] = str(m.group(2).replace(u'\xa0',u' '))
                                    substitution_data["field_position"] = str(m.group(3).replace(u'\xa0',u' '))
                                    substitution_data["batting_order"] = int(m.group(4).replace(u'\xa0',u' '))
                                elif i == 3:
                                    substitution_data["type"] = "defensive substitution"
                                    substitution_data["incoming_fielder"] = str(m.group(1).replace(u'\xa0',u' '))
                                    substitution_data["outgoing_fielder"] = str(m.group(2).replace(u'\xa0',u' '))
                                    substitution_data["outgoing_fielder_position"] = str(m.group(3).replace(u'\xa0',u' '))
                                    substitution_data["incoming_fielder_position"] = str(m.group(4).replace(u'\xa0',u' '))
                                    substitution_data["batting_order"] = int(m.group(5).replace(u'\xa0',u' '))
                                elif i == 4:
                                    substitution_data["type"] = "position change"
                                    substitution_data["moving_player"] = str(m.group(1).replace(u'\xa0',u' '))
                                    substitution_data["old_position"] = str(m.group(2).replace(u'\xa0',u' '))
                                    substitution_data["new_position"] = str(m.group(3).replace(u'\xa0',u' '))

                                subs_list.append(substitution_data)
                                event = event.replace(m.group(),"")
                                if len(event) < 15:
                                    break_out = True
                    else:
                        break
                play_by_play_data.append(("substitutions",subs_list))

            else:
                print "unknown class in play-by-play table"
        else:
            columns = row.find_all("td")
            event = columns[8].get_text()
            play_by_play_data.append(("miscellaneous event", event))
    return play_by_play_data

def scrape_pitching_data(pitching_html):
    overthrow = pitching_html.find("div", attrs={"class": "overthrow"})
    tbody = overthrow.find("tbody")
    rows = tbody.find_all("tr")
    
    pitching_data = {}

    for row in rows:
        player_data = {}
        name_and_result = row.find("th").get_text()
        m = re.search(r"(.*), (.*)", name_and_result)
        if m:
            player_name = m.group(1)
        else:
            player_name = name_and_result

        player_data["name"] = player_name

        pitching_stats = row.find_all("td")
        player_data["IP"] = pitching_stats[0].get_text()
        if player_data["IP"] != u'': player_data["IP"] = float(player_data["IP"])
        player_data["H"] = pitching_stats[1].get_text()
        if player_data["H"] != u'': player_data["H"] = int(player_data["H"])
        player_data["R"] = pitching_stats[2].get_text()
        if player_data["R"] != u'': player_data["R"] = int(player_data["R"])
        player_data["ER"] = pitching_stats[3].get_text()
        if player_data["ER"] != u'': player_data["ER"] = int(player_data["ER"])
        player_data["BB"] = pitching_stats[4].get_text()
        if player_data["BB"] != u'': player_data["BB"] = int(player_data["BB"])
        player_data["SO"] = pitching_stats[5].get_text()
        if player_data["SO"] != u'': player_data["SO"] = int(player_data["SO"])
        player_data["HR"] = pitching_stats[6].get_text()
        if player_data["HR"] != u'': player_data["HR"] = int(player_data["HR"])
        player_data["ERA"] = pitching_stats[7].get_text()
        if player_data["ERA"] != u'': player_data["ERA"] = float(player_data["ERA"])
        player_data["BF"] = pitching_stats[8].get_text()
        if player_data["BF"] != u'': player_data["BF"] = int(player_data["BF"])
        player_data["Pit"] = pitching_stats[9].get_text()
        if player_data["Pit"] != u'': player_data["Pit"] = int(player_data["Pit"])
        player_data["Str"] = pitching_stats[10].get_text()
        if player_data["Str"] != u'': player_data["Str"] = int(player_data["Str"])
        player_data["Ctct"] = pitching_stats[11].get_text()
        if player_data["Ctct"] != u'': player_data["Ctct"] = int(player_data["Ctct"])
        player_data["StS"] = pitching_stats[12].get_text()
        if player_data["StS"] != u'': player_data["StS"] = int(player_data["StS"])
        player_data["StL"] = pitching_stats[13].get_text()
        if player_data["StL"] != u'': player_data["StL"] = int(player_data["StL"])
        player_data["GB"] = pitching_stats[14].get_text()
        if player_data["GB"] != u'': player_data["GB"] = int(player_data["GB"])
        player_data["FB"] = pitching_stats[15].get_text()
        if player_data["FB"] != u'': player_data["FB"] = int(player_data["FB"])
        player_data["LD"] = pitching_stats[16].get_text()
        if player_data["LD"] != u'': player_data["LD"] = int(player_data["LD"])
        player_data["Unk"] = pitching_stats[17].get_text()
        if player_data["Unk"] != u'': player_data["Unk"] = int(player_data["Unk"])
        player_data["GSc"] = pitching_stats[18].get_text()
        if player_data["GSc"] != u'': player_data["GSc"] = int(player_data["GSc"])
        player_data["IR"] = pitching_stats[19].get_text()
        if player_data["IR"] != u'': player_data["IR"] = int(player_data["IR"])
        player_data["IS"] = pitching_stats[20].get_text()
        if player_data["IS"] != u'': player_data["IS"] = int(player_data["IS"])
        player_data["WPA"] = pitching_stats[21].get_text()
        if player_data["WPA"] != u'': player_data["WPA"] = float(player_data["WPA"])
        player_data["aLI"] = pitching_stats[22].get_text()
        if player_data["aLI"] != u'': player_data["aLI"] = float(player_data["aLI"])
        player_data["RE24"] = pitching_stats[23].get_text()
        if player_data["RE24"] != u'': player_data["RE24"] = float(player_data["RE24"])
        
        pitching_data[player_name] = player_data
    return pitching_data

def scrape_game_data(game_link):
    html = remove_comments(urllib2.urlopen(game_link).read())

    game_data = {}

    soup = BeautifulSoup(html, 'html.parser')
    linescore = soup.find("div", attrs={"class": "linescore_wrap"})
    box_data = scrape_box_data(linescore)

    game_data['box'] = box_data
    home_team_league = team_to_league[box_data["home"]["team_name"]]

    tables = soup.find_all("div", attrs={"class","table_wrapper"})
    away_batting_data = scrape_batting_data(tables[0])
    home_batting_data = scrape_batting_data(tables[1])
    away_pitching_data = scrape_pitching_data(tables[2])
    home_pitching_data = scrape_pitching_data(tables[3])
    # top_5_plays = scrape_top_5_plays_data(tables[4])
    play_by_play_data = scrape_play_by_play_data(tables[5], home_team_league)

    # section_wrappers = soup.find_all("div", attrs={"class","section_wrapper"})
    # other_games = section_wrappers[0]
    # pitching = section_wrappers[1]
    # other_info = section_wrappers[2]
    # win_probability_chart = section_wrappers[3]
    # play_by_play_explanation = section_wrappers[4]
    # pitching_content = pitching.find("div", attrs={"class", "table_outer_container"})

def remove_comments(text):
    text = re.sub(r"<!--(.*?)-->", '', text)
    text = text.replace("<!--","")
    text = text.replace("-->","")
    return text

def main():
    # box scores page from baseball-reference.com
    BOX_SCORES_PAGE = "https://www.baseball-reference.com/boxes"

    # test date and test page
    date = "/?month=7&day=24&year=2018"
    page = BOX_SCORES_PAGE+date

    # get the html using BeautifulSoup
    html = urllib2.urlopen(page)
    soup = BeautifulSoup(html.read(), "html.parser")

    # get a list of links of stats from each game
    game_links = []
    game_summary_list = soup.find_all('div', attrs={'class': 'game_summary nohover'})
    for game in game_summary_list:
        final_link = game.find('td', attrs={'class': 'right gamelink'})
        link = final_link.find('a').get('href')
        game_links.append(BOX_SCORES_PAGE+link[6:])

    for ind, game_link in enumerate(game_links):
        if ind == 10:
            scrape_game_data(game_link)

if __name__ == "__main__":
    main()



