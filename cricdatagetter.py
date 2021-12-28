import random
from sqlite3.dbapi2 import Cursor
import requests
from bs4 import BeautifulSoup
import sqlite3
from time import sleep

# TODO Add comments

db = sqlite3.connect("stats.db")
c: Cursor = db.cursor()

countries = {'ENG': "v England", 'IND': "v India", 'AUS': "v Australia", 'PAK': "v Pakistan", 'WI': "v West Indies",
             'SRI': "v Sri Lanka", 'AFG': "v Afghanistan", 'IRE': "v Ireland", 'RSA': "v South Africa", 'ZIM':
                 "v Zimbabwe", 'BAN': "Bangladesh", 'NZ': "v New Zealand", 'NED': "v Netherlands", 'UAE':
                 "v United Arab Emirates", 'USA': "v United States", 'NPL': "v Nepal", 'OMN': "v Oman",
             'NAM': "v Namibia",
             'PNG': "v Papua New Guinea"}

months = {"Jan": '01', "Feb": '02', "Mar": '03', "Apr": '04', "May": '05', "Jun": '06', "Jul": '07', "Aug": '08',
          "Sep": '09', "Oct": '10', "Nov": '11', "Dec": '12'}


def stats(matchnum):
    # Creates two tables one of the statistics for the batsmen and one for the bowlers, and gets the date, teams and
    # town.

    page = requests.get(
        "https://www.espncricinfo.com/matches/engine/match/" + matchnum + ".html")

    soup = BeautifulSoup(page.content, 'html.parser')

    battingtables = soup.find_all("table", class_="table batsman")
    bowlingtables = soup.find_all("table", class_="table bowler")

    batstats = []
    counter = -1

    for t in battingtables:
        batstats.append([])
        counter += 1

        body = t.find("tbody")

        rows = body.find_all("tr")

        batternum = -1
        for row in rows:
            batstats[counter].append([])
            batternum += 1

            for i, stat in enumerate(row):
                if i == 0:
                    stat = stat.text.replace("\xa0", "")
                    stat = stat.replace("(c)", "")
                    stat = stat.replace("†", "")
                    batstats[counter][batternum].append(stat)
                elif i == 1:
                    if stat == 'not out':
                        batstats[counter][batternum].append("1")  # 1 for not out
                    else:
                        batstats[counter][batternum].append("0")

                else:
                    batstats[counter][batternum].append(stat.text)

        batstats[counter].pop(-1)
        batstats[counter] = [x for x in batstats[counter] if x != ['']]

    bowlstats = []
    counter = -1

    for t in bowlingtables:
        bowlstats.append([])
        counter += 1

        body = t.find("tbody")

        rows = body.find_all("tr")

        bowlernum = -1
        for row in rows:
            bowlstats[counter].append([])
            bowlernum += 1

            for stat in row:
                bowlstats[counter][bowlernum].append(stat.text)

        bowlstats[counter].pop(-1)
        bowlstats[counter] = [x for x in bowlstats[counter] if x != ['']]

    description = soup.find("div", class_="description").text

    town = description.split(",")[1][1:]
    date = description.split(",")[2]
    date = date.split(" ")

    if len(date[2]) < 2:
        date[2] = '0' + date[2]

    datenum = date[-1] + "-" + months[date[1]] + "-" + date[2]

    teams = soup.find_all("div", class_="section-header border-bottom text-danger cursor-pointer")

    teamsarray = [team.text.split(" ")[0] for team in teams]

    return {"innings": [batstats, bowlstats], "date": datenum, "teams": list(set(teamsarray)),
            "batting_team": teamsarray, "town": town}


def matchnum_getter(matchformat):
    # This function creates a list of matches that need to be added to the database
    matches = []

    with open("completedmatches" + matchformat + ".txt", "r") as f:
        compmatches = f.read()

    with open("addedmatches" + matchformat + ".txt", "r") as f:
        for row in f:
            if row not in compmatches:
                matches.append(row[:-1])
    return matches


def match_data(matches, matchformat):
    for matchnum in matches:
        print("Now adding match number: " + matchnum)
        print()

        m = stats(matchnum)

        inningsnum = len(m["innings"][0])

        batting_team = m['batting_team']

        date = m['date']
        ground = m['town']

        print(date)
        print(ground)
        print()

        for i, innings in enumerate(m['innings'][0]):
            country = batting_team[i]
            if m['teams'][0] == country:
                opp = m['teams'][1]
            else:
                opp = m['teams'][0]

            for row in innings:
                if row[2] != "-": # checks for absences
                    # batting
                    # row [name, not out flag, runs, faced, mins, 4s, 6s, strike rate]

                    name = row[0]
                    notout = int(row[1])
                    runs = int(row[2])
                    runsnum = runs
                    faced = row[3]
                    mins = row[4]
                    fours = row[5]
                    sixes = row[6]
                    sr = row[7]

                    if runs < 50:
                        row50 = 0
                        row100 = 0
                    elif 50 <= runs < 100:
                        row50 = 1
                        row100 = 0
                    else:
                        row50 = 0
                        row100 = 1

                    if notout:
                        runs = str(runs) + "*"


                    query = "INSERT INTO {} (InningsPlayer, InningsRunsScored, InningsRunsScoredNum," \
                            " InningsMinutesBatted, InningsBattedFlag, InningsNotOutFlag, InningsBallsFaced, " \
                            "InningsBoundaryFours, InningsBoundarySixes, InningsBattingStrikeRate, InningsNumber," \
                            " Opposition, Ground, InningsDate, Country, '50s', '100s')" \
                            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)

                    c.execute(query,
                              [name, runs, runsnum, mins, 1, notout, faced, fours,
                               sixes, sr, i + 1, opp, ground, date, country, row50, row100])


        for i, innings in enumerate(m['innings'][1]):
            opp = batting_team[i]
            if m['teams'][0] == opp:
                country = m['teams'][1]
            else:
                country = m['teams'][0]

            for row in innings:
                # bowling
                # row [name, overs, maidens, runs, wickets, econ, wides, no balls]

                name = row[0]
                overs = row[1]
                maidens = row[2]
                conceded = row[3]
                wickets = int(row[4])
                eco = row[5]

                if wickets < 5:
                    wick4 = 1
                    wick5 = 0
                    wick10 = 0
                    buck = "0-4"
                elif 5 < wickets < 10:
                    wick4 = 0
                    wick5 = 1
                    wick10 = 0
                    buck = "5+"
                else:
                    wick4 = 0
                    wick5 = 0
                    wick10 = 1
                    buck = "5+"


                query = "INSERT INTO {} (InningsPlayer,InningsNumber,Opposition, Ground, InningsDate, Country," \
                        " InningsOversBowled, InningsBowledFlag, InningsMaidensBowled, " \
                        "InningsRunsConceded, InningsWicketsTaken, '4Wickets', '5Wickets', '10Wickets'," \
                        " InningsWicketsTakenBuckets, InningsEconomyRate)" \
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)
    
                c.execute(query, [name, i + 1, opp, ground, date, country, overs, 1, maidens, conceded, wickets,
                                  wick4, wick5, wick10, buck, eco])

        with open("completedmatches" + str(matchformat) + ".txt", "a") as f:
            print(matchnum, file=f)

        print("Finished adding match number: " + matchnum)
        sleeptime = random.uniform(1,3)
        print("Sleeping " + str(sleeptime) + " now")
        print("=========================================")
        sleep(sleeptime)


matches = matchnum_getter("Test")
match_data(matches, "Test")
matches = matchnum_getter("ODI")
match_data(matches, "ODI")

db.commit()

db.close()
