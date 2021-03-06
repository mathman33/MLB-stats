import urllib2
from bs4 import BeautifulSoup
import re
import os
import pickle
import time
from tqdm import tqdm

team_to_league = {
    'Los Angeles Dodgers': ['NL','west'],
    'Arizona Diamondbacks': ['NL','west'],
    'San Francisco Giants': ['NL','west'],
    'Colorado Rockies': ['NL','west'],
    'San Diego Padres': ['NL','west'],
    'Chicago Cubs': ['NL','central'],
    'St. Louis Cardinals': ['NL','central'],
    'Cincinnati Reds': ['NL','central'],
    'Pittsburgh Pirates': ['NL','central'],
    'Milwaukee Brewers': ['NL','central'],
    'Miami Marlins': ['NL','east'],
    'New York Mets': ['NL','east'],
    'Washington Nationals': ['NL','east'],
    'Atlanta Braves': ['NL','east'],
    'Philadelphia Phillies': ['NL','east'],
    'Los Angeles Angels': ['AL','west'],
    'Oakland Athletics': ['AL','west'],
    'Texas Rangers': ['AL','west'],
    'Seattle Mariners': ['AL','west'],
    'Houston Astros': ['AL','west'],
    'Chicago White Sox': ['AL','central'],
    'Cleveland Indians': ['AL','central'],
    'Detroit Tigers': ['AL','central'],
    'Kansas City Royals': ['AL','central'],
    'Minnesota Twins': ['AL','central'],
    'Boston Red Sox': ['AL','east'],
    'Baltimore Orioles': ['AL','east'],
    'Tampa Bay Rays': ['AL','east'],
    'New York Yankees': ['AL','east'],
    'Toronto Blue Jays': ['AL','east']
}

team_to_stamp = {
    # National League
        # West
            'Los Angeles Dodgers': 'LAD',
            'Arizona Diamondbacks': 'ARI',
            'San Francisco Giants': 'SFG',
            'Colorado Rockies': 'COL',
            'San Diego Padres': 'SDP',
        # Central
            'Chicago Cubs': 'CHC',
            'St. Louis Cardinals': 'STL',
            'Cincinnati Reds': 'CIN',
            'Pittsburgh Pirates': 'PIT',
            'Milwaukee Brewers': 'MIL',
        # East
            'Miami Marlins': 'FLA',
            'New York Mets': 'NYM',
            'Washington Nationals': 'WSN',
            'Atlanta Braves': 'ATL',
            'Philadelphia Phillies': 'PHI',
    # American League
        # West
            'Los Angeles Angels': 'ANA',
            'Oakland Athletics': 'OAK',
            'Texas Rangers': 'TEX',
            'Seattle Mariners': 'SEA',
            'Houston Astros': 'HOU',
        # Central
            'Chicago White Sox': 'CHW',
            'Cleveland Indians': 'CLE',
            'Detroit Tigers': 'DET',
            'Kansas City Royals': 'KCR',
            'Minnesota Twins': 'MIN',
        # East
            'Boston Red Sox': 'BOS',
            'Baltimore Orioles': 'BAL',
            'Tampa Bay Rays': 'TBD',
            'New York Yankees': 'NYY',
            'Toronto Blue Jays': 'TOR'
}

def scrape_box_data(linescore):
    box_data = {'away':{},'home':{}}

    teams_soup = linescore.find('tbody')
    teams_list = teams_soup.find_all('tr')

    away_team_box = teams_list[0].find_all('td')
    box_data['away']['team_name'] = str(away_team_box[1].get_text())
    away_team_innings = []
    for i in xrange(2,len(away_team_box)-3):
        away_team_innings.append(str(away_team_box[i].get_text()))
    box_data['away']['innings'] = away_team_innings
    box_data['away']['runs'] = int(away_team_box[-3].get_text())
    box_data['away']['hits'] = int(away_team_box[-2].get_text())
    box_data['away']['errors'] = int(away_team_box[-1].get_text())

    home_team_box = teams_list[1].find_all('td')
    box_data['home']['team_name'] = str(home_team_box[1].get_text())
    home_team_innings = []
    for i in xrange(2,len(home_team_box)-3):
        home_team_innings.append(str(home_team_box[i].get_text()))
    box_data['home']['innings'] = home_team_innings
    box_data['home']['runs'] = int(home_team_box[-3].get_text())
    box_data['home']['hits'] = int(home_team_box[-2].get_text())
    box_data['home']['errors'] = int(home_team_box[-1].get_text())

    box_data['winning_team'] = box_data['away']['team_name'] if box_data['away']['runs'] > box_data['home']['runs'] else box_data['home']['team_name']
    box_data['losing_team'] = box_data['away']['team_name'] if box_data['away']['runs'] < box_data['home']['runs'] else box_data['home']['team_name']

    bottom_text_soup = linescore.find('tfoot')
    bottom_text_list = bottom_text_soup.find_all('tr')
    
    t = bottom_text_list[0].get_text()
    m = re.search(r'WP:.(.*).\(\d{1,2}-\d{1,2}\).{3}LP:.(.*).\(\d{1,2}-\d{1,2}\)(.?.?.?S?V?:?.?(.*)?.+?\(\d{1,2}\)?)?', t)
    box_data['winning_pitcher'] = m.group(1)
    box_data['losing_pitcher'] = m.group(2)
    if len(m.groups()) == 4:
        box_data['saving_pitcher'] = m.group(4)

    if len(bottom_text_list) > 1:
        box_data['extra_text'] = str(bottom_text_list[1].get_text())
    else:
        box_data['extra_text'] = ''

    return box_data

def scrape_batting_data(batting_html):
    overthrow = batting_html.find('div', attrs={'class': 'overthrow'})
    tbody = overthrow.find('tbody')
    rows = tbody.find_all('tr')

    batting_data = {}

    for row in rows:
        if not row.has_attr('class'):
            player_data = {}
            name_and_position = row.find('th').get_text()
            m = re.search(r'(.*) (.*)', name_and_position)
            player_name = str(m.group(1).replace(u'\xa0',u''))
            player_position = str(m.group(2))

            player_data['position'] = player_position

            batting_stats = row.find_all('td')

            AB = batting_stats[0].get_text()
            player_data['AB'] = int(AB) if AB != u'' else ''
            R = batting_stats[1].get_text()
            player_data['R'] = int(R) if R != u'' else ''
            H = batting_stats[2].get_text()
            player_data['H'] = int(H) if H != u'' else ''
            RBI = batting_stats[3].get_text()
            player_data['RBI'] = int(RBI) if RBI != u'' else ''
            BB = batting_stats[4].get_text()
            player_data['BB'] = int(BB) if BB != u'' else ''
            SO = batting_stats[5].get_text()
            player_data['SO'] = int(SO) if SO != u'' else ''
            PA = batting_stats[6].get_text()
            player_data['PA'] = int(PA) if PA != u'' else ''
            BA = batting_stats[7].get_text()
            player_data['BA'] = float(BA) if BA != u'' else ''
            OBP = batting_stats[8].get_text()
            player_data['OBP'] = float(OBP) if OBP != u'' else ''
            SLG = batting_stats[9].get_text()
            player_data['SLG'] = float(SLG) if SLG != u'' else ''
            OPS = batting_stats[10].get_text()
            player_data['OPS'] = float(OPS) if OPS != u'' else ''
            Pit = batting_stats[11].get_text()
            player_data['Pit'] = int(Pit) if Pit != u'' else ''
            Str = batting_stats[12].get_text()
            player_data['Str'] = int(Str) if Str != u'' else ''
            WPA = batting_stats[13].get_text()
            player_data['WPA'] = float(WPA) if WPA != u'' else ''
            aLI = batting_stats[14].get_text()
            player_data['aLI'] = float(aLI) if aLI != u'' else ''
            WPA = batting_stats[15].get_text()
            player_data['WPA+'] = float(WPA) if WPA != u'' else ''
            WPA = batting_stats[16].get_text()
            player_data['WPA-'] = float(WPA) if WPA != u'' else ''
            RE24 = batting_stats[17].get_text()
            player_data['RE24'] = float(RE24) if RE24 != u'' else ''
            PO = batting_stats[18].get_text()
            player_data['PO'] = int(PO) if PO != u'' else ''
            A = batting_stats[19].get_text()
            player_data['A'] = int(A) if A != u'' else ''
            
            player_data['Details'] = str(batting_stats[20].get_text().replace(u'\xb7',u''))

            batting_data[player_name] = player_data
    return batting_data

def scrape_play_by_play_data(play_by_play_html, home_team_league, names):
    # print names
    regex_names = '|'.join(names)
    
    overthrow = play_by_play_html.find('div', attrs={'class': 'overthrow'})
    tbody = overthrow.find('tbody')
    rows = tbody.find_all('tr')

    pitching_substitution_pattern = r'(%s) replaces (%s)( \((1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH)\))? pitching( and batting (\d)(th|rd|st|nd)+)?' % (regex_names,regex_names)
    pinch_hitter_pattern = r'(%s) pinch hits for (%s)( \((1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH)\))? batting (\d)(th|rd|st|nd)+?' % (regex_names,regex_names)
    pinch_runner_pattern = r'(%s) pinch runs for (%s) \((1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH)\) batting (\d)(th|rd|st|nd)+?' % (regex_names,regex_names)
    fielding_substitution_pattern = r'(%s) replaces (%s)( \((1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH)\))? playing (1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH) batting (\d)(th|rd|st|nd)+?' % (regex_names,regex_names)
    move_pattern = r'(%s) moves from (1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH) to (1B|2B|3B|SS|LF|RF|C|CF|P|PH|PR|DH)+?( \(team loses DH\))?' % regex_names
    american_league_DH_substitution_pattern = r'(%s) pinch hit for DH and is now DH' % regex_names
    substitution_patterns = [pitching_substitution_pattern,
                             pinch_hitter_pattern,
                             pinch_runner_pattern,
                             fielding_substitution_pattern,
                             move_pattern]
    if home_team_league[0] == 'AL':
        substitution_patterns.append(american_league_DH_substitution_pattern)

    play_by_play_data = []

    for row in rows:
        if row.has_attr('class'):
            if row['class'][0] == u'pbp_summary_top':
                half_inning_summary = row.get_text()
                m = re.search(r'(Top|Bottom) of the (\d{1,2})(th|rd|st|nd), (.*) Batting, (Tied|Ahead|Behind) (\d{1,2})-(\d{1,2}), (.*)\' (.*) facing (\d-\d-\d)', half_inning_summary)
                top_or_bottom = str(m.group(1))
                inning = int(m.group(2))
                batting_team = str(m.group(4))
                batting_team_tied_ahead_behind = str(m.group(5))
                batting_team_score = int(m.group(6))
                pitching_team_score = int(m.group(7))
                pitching_team = str(m.group(8))
                pitcher = str(m.group(9).replace(u'\xa0',u' '))
                batting_order = str(m.group(10))

                pre_half_inning_summary = {
                    'top_or_bottom': top_or_bottom,
                    'inning': inning,
                    'batting_team': batting_team,
                    'batting_team_tied_ahead_behind': batting_team_tied_ahead_behind,
                    'batting_team_score': batting_team_score,
                    'pitching_team_score': pitching_team_score,
                    'pitching_team': pitching_team,
                    'pitcher': pitcher,
                    'batting_order': batting_order
                }
                play_by_play_data.append(['pre_half_inning_summary',pre_half_inning_summary])

            elif row['class'][0] == u'pbp_summary_bottom':
                half_inning_summary = row.get_text()
                m = re.search(r'(.*) runs?, (.*) hits?, (.*) errors?, (.*) LOB. (.*) (.*), (.*) (.*).', half_inning_summary)
                runs = int(m.group(1))
                hits = int(m.group(2))
                errors = int(m.group(3))
                LOB = int(m.group(4))
                away_team = str(m.group(5))
                away_team_score = int(m.group(6))
                home_team = str(m.group(7))
                home_team_score = int(m.group(8))

                post_half_inning_summary = {
                    'runs': runs,
                    'hits': hits,
                    'errors': errors,
                    'LOB': LOB,
                    'away_team': away_team,
                    'away_team_score': away_team_score,
                    'home_team': home_team,
                    'home_team_score': home_team_score
                }
                play_by_play_data.append(['post_half_inning_summary',post_half_inning_summary])

            elif u'top_inning' in row['class'][0] or u'bottom_inning' in row['class'][0]:
                columns = row.find_all('td')
                pre_AB_score = columns[0].get_text()
                m = re.search(r'(.*)-(.*)', pre_AB_score)
                pre_AB_batting_team_score = int(m.group(1))
                pre_AB_pitching_team_score = int(m.group(2))
                outs = int(columns[1].get_text())
                runners = str(columns[2].get_text())
                pitches = columns[3].get_text()
                m = re.search(r'(\d{1,2}),\((\d)-(\d)\)',pitches)
                if m == None:
                    if pitches == u'':
                        num_pitches = 0
                        balls_at_event = 0
                        strikes_at_event = 0
                    else:
                        m = re.search(r',\((\d)-(\d)\)',pitches)
                        balls_at_event = int(m.group(1))
                        strikes_at_event = int(m.group(2))
                        num_pitches = balls_at_event + strikes_at_event
                else:
                    num_pitches = int(m.group(1))
                    balls_at_event = int(m.group(2))
                    strikes_at_event = int(m.group(3))
                runs_and_outs = columns[4].get_text()
                resulting_runs = int(runs_and_outs.count('R'))
                resulting_outs = int(runs_and_outs.count('O'))
                batting_teamstamp = str(columns[5].get_text())
                batter = str(columns[6].get_text().replace(u'\xa0',u' '))
                pitcher = str(columns[7].get_text().replace(u'\xa0',u' '))
                wWPA_text = columns[8].get_text()
                m = re.search(r'(.*)\%', wWPA_text)
                wWPA = int(m.group(1))
                wWE_text = columns[9].get_text()
                m = re.search(r'(.*)\%', wWE_text)
                wWE = int(m.group(1))
                description = str(columns[10].get_text().replace(u'\xa0',u' '))
                events = description.split('; ')
                events = [str(e.replace(u'\xa0',u' ')) for e in events]
                score = str(u'bold' in row['class'])

                batter = {
                    'pre_AB_batting_team_score': pre_AB_batting_team_score,
                    'pre_AB_pitching_team_score': pre_AB_pitching_team_score,
                    'outs': outs,
                    'runners': runners,
                    'num_pitches': num_pitches,
                    'balls_at_event': balls_at_event,
                    'strikes_at_event': strikes_at_event,
                    'resulting_runs': resulting_runs,
                    'resulting_outs': resulting_outs,
                    'batting_teamstamp': batting_teamstamp,
                    'batter': batter,
                    'pitcher': pitcher,
                    'wWPA': wWPA,
                    'wWE': wWE,
                    'events': events,
                    'score': score
                }
                play_by_play_data.append(['batter',batter])
            
            elif row['class'][0] == u'ingame_substitution':
                columns = row.find_all('td')
                event = columns[8].get_text().replace(u'\xa0',u' ')
                num_subs = event.count('replaces') + event.count('moves') + event.count('pinch hit') + event.count('pinch run')


                subs_list = []
                
                break_out = False
                count = 0
                while True:
                    count += 1
                    if count > 500:
                        print 'unable to parse play-by-play table'
                        break
                    if not break_out:
                        for i, pattern in enumerate(substitution_patterns):
                            m = re.search(pattern, event)
                            # print event
                            if m:
                                substitution_data = {}
                                if i == 0:
                                    substitution_data['type'] = 'pitching change'
                                    substitution_data['incoming_pitcher'] = str(m.group(1))
                                    substitution_data['outgoing_pitcher'] = str(m.group(2))
                                    if m.group(4) != None:
                                        substitution_data['outgoing_position'] = str(m.group(4))
                                    if m.group(6) != None:
                                        substitution_data['batting_order'] = int(m.group(6))
                                elif i == 1:
                                    substitution_data['type'] = 'pinch hitter'
                                    substitution_data['pinch_hitter'] = str(m.group(1))
                                    substitution_data['outgoing_hitter'] = str(m.group(2))
                                    substitution_data['field_position'] = str(m.group(4))
                                    substitution_data['batting_order'] = int(m.group(5))
                                elif i == 2:
                                    substitution_data['type'] = 'pinch runner'
                                    substitution_data['pinch_runner'] = str(m.group(1))
                                    substitution_data['outgoing_runner'] = str(m.group(2))
                                    substitution_data['field_position'] = str(m.group(3))
                                    substitution_data['batting_order'] = int(m.group(4))
                                elif i == 3:
                                    substitution_data['type'] = 'defensive substitution'
                                    substitution_data['incoming_fielder'] = str(m.group(1))
                                    substitution_data['outgoing_fielder'] = str(m.group(2))
                                    if len(m.groups()) == 7:
                                        substitution_data['incoming_fielder_position'] = str(m.group(5))
                                        substitution_data['batting_order'] = int(m.group(6))
                                    else:
                                        substitution_data['outgoing_fielder_position'] = str(m.group(3))
                                        substitution_data['incoming_fielder_position'] = str(m.group(4))
                                        substitution_data['batting_order'] = int(m.group(5))
                                elif i == 4:
                                    substitution_data['type'] = 'position change'
                                    substitution_data['moving_player'] = str(m.group(1))
                                    substitution_data['old_position'] = str(m.group(2))
                                    substitution_data['new_position'] = str(m.group(3))
                                    if m.group(4) != None:
                                        substitution_data['extra_text'] = str(m.group(4))
                                elif i == 5:
                                    substitution_data['type'] = 'AL DH substitution'
                                    substitution_data['moving player'] = str(m.group(1))

                                subs_list.append(substitution_data)
                                event = event.replace(m.group(),'')
                                if len(event) < 15:
                                    break_out = True
                    else:
                        break
                if len(subs_list) != num_subs:
                    print 'error regexing'
                    print subs_list
                    print '\n\n\n\n\n\n\n\n\n'
                    time.sleep(1)
                    raise
                play_by_play_data.append(['substitutions',subs_list])

            else:
                print 'unknown class in play-by-play table'
        else:
            columns = row.find_all('td')
            event = str(columns[8].get_text().replace(u'\xa0',u' '))
            play_by_play_data.append(['miscellaneous event', event])
    return play_by_play_data

def scrape_indiv_pitching_events_data(indiv_events_html):
    indiv_events = indiv_events_html.find('div').find_all('div')
    
    # balks
    balks = {}
    m = re.search(r'Balks: (.*)',indiv_events[0].get_text())
    balks_text = m.group(1)
    if balks_text != u'None.':
        balks_text_list = balks_text.split('; ')
        for balks_t in balks_text_list:
            m = re.search(r'(.*) ?(\d*) \(\d+\)',balks_t)
            pitcher_name = str(m.group(1).replace(u'\xa0',' '))
            if len(m.group(2)) == 0:
                num_balks = 1
            else:
                num_balks = int(m.group(2))
            balks[pitcher_name] = num_balks

    # wild pitches
    wild_pitches = {}
    m = re.search(r'WP: (.*)',indiv_events[1].get_text())
    WP_text = m.group(1)
    if WP_text != u'None.':
        WP_text_list = WP_text.split('); ')
        for WP_t in WP_text_list:
            m = re.search(r'((.*)( )(\d)|.*) \(\d+\)?',WP_t)
            if m.group(4) == None:
                pitcher_name = str(m.group(1).replace(u'\xa0',u' '))
                num_WP = 1
            else:
                pitcher_name = str(m.group(2).replace(u'\xa0',u' '))
                num_WP = int(m.group(4))
            wild_pitches[pitcher_name] = num_WP

    # hit by pitch
    hit_by_pitch = {}
    m = re.search(r'HBP: (.*)',indiv_events[2].get_text())
    HBP_text = m.group(1)
    if HBP_text != u'None.':
        HBP_text_list = HBP_text.split('); ')
        for HBP_t in HBP_text_list:
            m = re.search(r'((.*)( )(\d)|.*) \(\d+; (.*)\)?',HBP_t)
            if m.group(4) == None:
                pitcher_name = str(m.group(1).replace(u'\xa0',u' '))
                num_HBP = 1
            else:
                pitcher_name = str(m.group(2).replace(u'\xa0',u' '))
                num_HBP = int(m.group(4))
            batters = m.group(5)[:-2]
            batters = str(batters.replace(u'\xa0',u' '))
            batters = batters.split(', ')
            hit_by_pitch[pitcher_name] = {'num_HBP': num_HBP, 'batters': batters}

    # intentional_BB
    intentional_BB = {}
    m = re.search(r'IBB: (.*)',indiv_events[3].get_text())
    IBB_text = m.group(1)
    if IBB_text != u'None.':
        IBB_text_list = IBB_text.split('); ')
        for IBB_t in IBB_text_list:
            m = re.search(r'((.*)( )(\d)|.*) \(\d+; (.*)\)?', IBB_t)
            if m.group(4) == None:
                pitcher_name = str(m.group(1).replace(u'\xa0',u' '))
                num_IBB = 1
            else:
                pitcher_name = str(m.group(2).replace(u'\xa0',u' '))
                num_IBB = int(m.group(4))
            batters = m.group(5)[:-2]
            batters = str(batters.replace(u'\xa0',u' '))
            batters = batters.split(', ')
            intentional_BB[pitcher_name] = {'num_IBB': num_IBB, 'batters': batters}

    # pickoffs
    pickoffs = {}
    m = re.search(r'Pickoffs: (.*)',indiv_events[4].get_text())
    pickoffs_text = m.group(1)
    if pickoffs_text != u'None.':
        pickoffs_list = pickoffs_text.split('); ')
        for pickoffs_t in pickoffs_list:
            m = re.search(r'((.*)( )(\d)|.*) \(\d+; (.*)\)?', pickoffs_t)
            if m.group(4) == None:
                pitcher_name = str(m.group(1).replace(u'\xa0',u' '))
                num_pickoffs = 1
            else:
                pitcher_name = str(m.group(2).replace(u'\xa0',u' '))
                num_pickoffs = int(m.group(4))
            batters_and_locations = str(m.group(5).replace(u'\xa0',u' '))
            batters_and_locations_list = batters_and_locations.split(', ')
            batters = batters_and_locations_list[::2]
            locations = [a.replace('base)','base').replace('CS))','CS)').replace('.','') for a in batters_and_locations_list[1::2]]
            pickoffs[pitcher_name] = {'num_pickoffs': num_pickoffs, 'batters': batters, 'locations': locations}
    return {'balks': balks, 'wild_pitches': wild_pitches, 'intentional_BB': intentional_BB, 'pickoffs': pickoffs, 'hit_by_pitch': hit_by_pitch}

def scrape_pitching_data(pitching_html,indiv_events):
    overthrow = pitching_html.find('div', attrs={'class': 'overthrow'})
    tbody = overthrow.find('tbody')
    rows = tbody.find_all('tr')
    
    balks = indiv_events['balks']
    wild_pitches = indiv_events['wild_pitches']
    intentional_BB = indiv_events['intentional_BB']
    pickoffs = indiv_events['pickoffs']
    hit_by_pitch = indiv_events['hit_by_pitch']

    pitching_data = {}

    for row in rows:
        player_data = {}
        name_and_result = row.find('th').get_text()
        player_name = str(name_and_result.split(',')[0])
        player_data['name'] = player_name
        if player_name in balks:
            player_data['balks'] = balks[player_name]
        if player_name in wild_pitches:
            player_data['wild_pitches'] = wild_pitches[player_name]
        if player_name in hit_by_pitch:
            player_data['hit_by_pitch'] = hit_by_pitch[player_name]
        if player_name in intentional_BB:
            player_data['intentional_BB'] = intentional_BB[player_name]
        if player_name in pickoffs:
            player_data['pickoffs'] = pickoffs[player_name]

        pitching_stats = row.find_all('td')

        IP = pitching_stats[0].get_text()
        player_data['IP'] = float(IP) if IP != u'' else ''
        H = pitching_stats[1].get_text()
        player_data['H'] = int(H) if H != u'' else ''
        R = pitching_stats[2].get_text()
        player_data['R'] = int(R) if R != u'' else ''
        ER = pitching_stats[3].get_text()
        player_data['ER'] = int(ER) if ER != u'' else ''
        BB = pitching_stats[4].get_text()
        player_data['BB'] = int(BB) if BB != u'' else ''
        SO = pitching_stats[5].get_text()
        player_data['SO'] = int(SO) if SO != u'' else ''
        HR = pitching_stats[6].get_text()
        player_data['HR'] = int(HR) if HR != u'' else ''
        ERA = pitching_stats[7].get_text()
        player_data['ERA'] = float(ERA) if ERA != u'' else ''
        BF = pitching_stats[8].get_text()
        player_data['BF'] = int(BF) if BF != u'' else ''
        Pit = pitching_stats[9].get_text()
        player_data['Pit'] = int(Pit) if Pit != u'' else ''
        Str = pitching_stats[10].get_text()
        player_data['Str'] = int(Str) if Str != u'' else ''
        Ctct = pitching_stats[11].get_text()
        player_data['Ctct'] = int(Ctct) if Ctct != u'' else ''
        StS = pitching_stats[12].get_text()
        player_data['StS'] = int(StS) if StS != u'' else ''
        StL = pitching_stats[13].get_text()
        player_data['StL'] = int(StL) if StL != u'' else ''
        GB = pitching_stats[14].get_text()
        player_data['GB'] = int(GB) if GB != u'' else ''
        FB = pitching_stats[15].get_text()
        player_data['FB'] = int(FB) if FB != u'' else ''
        LD = pitching_stats[16].get_text()
        player_data['LD'] = int(LD) if LD != u'' else ''
        Unk = pitching_stats[17].get_text()
        player_data['Unk'] = int(Unk) if Unk != u'' else ''
        GSc = pitching_stats[18].get_text()
        player_data['GSc'] = int(GSc) if GSc != u'' else ''
        IR = pitching_stats[19].get_text()
        player_data['IR'] = int(IR) if IR != u'' else ''
        IS = pitching_stats[20].get_text()
        player_data['IS'] = int(IS) if IS != u'' else ''
        WPA = pitching_stats[21].get_text()
        player_data['WPA'] = float(WPA) if WPA != u'' else ''
        aLI = pitching_stats[22].get_text()
        player_data['aLI'] = float(aLI) if aLI != u'' else ''
        RE24 = pitching_stats[23].get_text()
        player_data['RE24'] = float(RE24) if RE24 != u'' else ''

        pitching_data[player_name] = player_data
    return pitching_data

def get_names(b1, b2, p1, p2):
    names = list(set((b1.keys() + b2.keys() + p1.keys() + p2.keys())))
    with open('nicknames.txt','r') as f:
        nickname_contents = f.read()
    nicknames = []
    for name in names:
        if name in nickname_contents:
            m = re.search(r'%s=(.*)'%name, nickname_contents)
            if m == None:
                m = re.search(r'(.*)=%s'%name, nickname_contents)
            nicknames.append(m.group(1))
    return list(set(names+nicknames))

def scrape_game_data(game_link):
    html = remove_comments(urllib2.urlopen(game_link).read())

    game_data = {}

    soup = BeautifulSoup(html, 'html.parser')
    linescore = soup.find('div', attrs={'class': 'linescore_wrap'})
    box_data = scrape_box_data(linescore)

    game_data['box'] = box_data
    home_team_league = team_to_league[box_data['home']['team_name']]

    tables = soup.find_all('div', attrs={'class':'table_wrapper'})
    indiv_events = soup.find('div', attrs={'class':'indiv_events'})
    away_batting_data = scrape_batting_data(tables[0])
    home_batting_data = scrape_batting_data(tables[1])
    indiv_pitching_data = scrape_indiv_pitching_events_data(indiv_events)
    away_pitching_data = scrape_pitching_data(tables[2],indiv_pitching_data)
    home_pitching_data = scrape_pitching_data(tables[3],indiv_pitching_data)
    names = get_names(away_batting_data,home_batting_data,away_pitching_data,home_pitching_data)
    # top_5_plays = scrape_top_5_plays_data(tables[4])
    play_by_play_data = scrape_play_by_play_data(tables[5], home_team_league, names)

    game_data['away_batting'] = away_batting_data
    game_data['home_batting'] = home_batting_data
    game_data['away_pitching'] = away_pitching_data
    game_data['home_pitching'] = home_pitching_data
    game_data['play_by_play'] = play_by_play_data

    return game_data

def remove_comments(text):
    text = re.sub(r'<!--(.*?)-->', '', text)
    text = text.replace('<!--','')
    text = text.replace('-->','')
    return text

def save_data(game_link_filename,game_data,date):
    src = os.path.join('game_stats','all_games',str(game_link_filename))
    src_full = os.path.abspath(src)

    pickle.dump(game_data, open(src, 'wb' ) )

    home_team = game_data['box']['home']['team_name']
    away_team = game_data['box']['away']['team_name']
    home_team_stamp = team_to_stamp[home_team]
    home_team_league = team_to_league[home_team]
    away_team_stamp = team_to_stamp[away_team]
    away_team_league = team_to_league[away_team]
    m = re.search(r'/?month=(\d{1,2})&day=(\d{1,2})&year=(\d{4})',date)
    month = int(m.group(1))
    day = int(m.group(2))
    year = int(m.group(3))

    by_home_team_dir = os.path.join('game_stats','by_team',home_team_league[0],home_team_league[1],home_team_stamp)
    by_away_team_dir = os.path.join('game_stats','by_team',away_team_league[0],away_team_league[1],away_team_stamp)
    by_date_dir = os.path.join('game_stats','by_date','%d'%year,'%02d'%month,'%02d'%day)        
    if not os.path.isdir(by_home_team_dir):
        os.makedirs(by_home_team_dir)
    if not os.path.isdir(by_away_team_dir):
        os.makedirs(by_away_team_dir)
    if not os.path.isdir(by_date_dir):
        os.makedirs(by_date_dir)

    # https://www.baseball-reference.com/boxes/LAN/LAN201903280.shtml
    home_path = os.path.join(by_home_team_dir,game_link_filename)
    away_path = os.path.join(by_away_team_dir,game_link_filename)
    date_path = os.path.join(by_date_dir,game_link_filename)
    if os.path.islink(home_path):
        os.unlink(home_path)
    if os.path.islink(away_path):
        os.unlink(away_path)
    if os.path.islink(date_path):
        os.unlink(date_path)
    os.symlink(src_full,home_path)
    os.symlink(src_full,away_path)
    os.symlink(src_full,date_path)

def main():
    # box scores page from baseball-reference.com
    BOX_SCORES_PAGE = 'https://www.baseball-reference.com/boxes'

    # test date and test page
    date = '/?month=3&day=28&year=2019'
    page = BOX_SCORES_PAGE+date

    # get the html using BeautifulSoup
    html = urllib2.urlopen(page)
    soup = BeautifulSoup(html.read(), 'html.parser')

    # get a list of links of stats from each game
    game_links = []
    game_summary_list = soup.find_all('div', attrs={'class': 'game_summary nohover'})
    for game in game_summary_list:
        final_link = game.find('td', attrs={'class': 'right gamelink'})
        link = final_link.find('a').get('href')
        game_links.append(BOX_SCORES_PAGE+link[6:])

    for ind, game_link in tqdm(enumerate(game_links)):
        # if ind == 13:
        game_data = scrape_game_data(game_link)

        game_link_filename = (game_link.replace(BOX_SCORES_PAGE+'/','').replace('.shtml','')+'.p')[4:]
        save_data(game_link_filename,game_data,date)




if __name__ == '__main__':
    main()



