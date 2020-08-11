from sqlite3.dbapi2 import Cursor
from espncricinfo.match import Match
import sqlite3
from time import sleep

# TODO Add comments

db = sqlite3.connect("C:/Users/olism/Projects/cricket-site/stats.db")
c: Cursor = db.cursor()

countries = {'ENG': "v England", 'IND': "v India", 'AUS': "v Australia", 'PAK': "v Pakistan", 'WI': "v West Indies",
               'SRI': "v Sri Lanka", 'AFG': "v Afghanistan", 'IRE': "v Ireland", 'RSA': "v South Africa", 'ZIM':
                   "v Zimbabwe", 'BAN': "Bangladesh", 'NZ': "v New Zealand", 'NED': "v Netherlands", 'UAE':
             "v United Arab Emirates", 'USA': "v United States", 'NPL': "v Nepal", 'OMN': "v Oman", 'NAM': "v Namibia",
             'PNG': "v Papua New Guinea"}

def matchnum_getter(matchformat):
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

        m = Match(str(matchnum))

        if matchformat == "Test":
            inningsnum = 4
        else:
            inningsnum = 2

        date = m.date
        ground = m.town_name
        names1 = []
        names2 = []
        for row in m.team_1_players:
            names1.append(row['card_long'])

        for row in m.team_2_players:
            names2.append(row['card_long'])

        for i in range(inningsnum):
            for row in m.all_innings[i]['batsmen']:
                name = row['name']

                if name in names1:
                    country = countries[m.team_1_abbreviation][2:]
                    opp = countries[m.team_2_abbreviation]
                else:
                    country = countries[m.team_2_abbreviation][2:]
                    opp = countries[m.team_1_abbreviation]

                runs = int(row['runs'])
                runsnum = runs
                mins = row['minutes']
                notout = int(row['isNotOut'])
                faced = row['ballsFaced']
                fours = row['fours']
                sixes = row['sixes']
                sr = row['strikeRate']

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

                query = "INSERT INTO {} (InningsPlayer, InningsRunsScored, InningsRunsScoredNum,"\
                        " InningsMinutesBatted, InningsBattedFlag, InningsNotOutFlag, InningsBallsFaced, "\
                        "InningsBoundaryFours, InningsBoundarySixes, InningsBattingStrikeRate, InningsNumber,"\
                        " Opposition, Ground, InningsDate, Country, '50s', '100s')"\
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)

                c.execute(query,
                          [name, runs, runsnum, mins, 1, notout, faced, fours,
                           sixes, sr, i + 1, opp, ground, date, country, row50, row100])

        for i in range(inningsnum):
            for row in m.all_innings[i]['didNotBat']:
                if row != None:
                    name = row['name']
                    query = "INSERT INTO {} (InningsPlayer, InningsRunsScored, InningsBattedFlag, InningsNotOutFlag," \
                            " InningsNumber, Opposition, Ground, InningsDate, Country, '50s', '100s') "\
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)

                    c.execute(query, [name, "DNB", 0, 0, i + 1, opp, ground, date, country, 0, 0])

        for i in range(inningsnum):
            bowlers = []
            for row in m.all_innings[i]['bowlers']:
                name = row['name']

                if name in names1:
                    country = countries[m.team_1_abbreviation][2:]
                    opp = countries[m.team_2_abbreviation]
                else:
                    country = countries[m.team_2_abbreviation][2:]
                    opp = countries[m.team_1_abbreviation]

                bowlers.append(name)
                overs = row['overs']
                maidens = row['maidens']
                conceded = row['conceded']
                wickets = int(row['wickets'])
                eco = row['economyRate']

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

                query = "INSERT INTO {} (InningsPlayer,InningsNumber,Opposition, Ground, InningsDate, Country,"\
                          " InningsOversBowled, InningsBowledFlag, InningsMaidensBowled, "\
                          "InningsRunsConceded, InningsWicketsTaken, '4Wickets', '5Wickets', '10Wickets',"\
                          " InningsWicketsTakenBuckets, InningsEconomyRate)" \
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)

                c.execute(query,[name, i + 1, opp, ground, date, country, overs, 1, maidens, conceded, wickets,
                                 wick4, wick5, wick10, buck, eco])

            if m.all_innings[i]['bowlers'][0]['name'] in names1:
                nameset = names1
            else:
                nameset = names2

            for name in nameset:
                if name not in bowlers:

                    query = "INSERT INTO {} (InningsPlayer, InningsNumber, Opposition, Ground, InningsDate," \
                            " Country, InningsOversBowled, InningsBowledFlag, '4wickets', '5wickets', '10wickets')" \
                            " VALUES (?,?,?,?,?,?,?,?,?,?,?)".format(matchformat)

                    c.execute(query, [name, i + 1, opp, ground, date, country, 'DNB', 0, 1, 0, 0])

        with open("completedmatches" + str(matchformat) + ".txt", "a") as f:
            print(matchnum, file=f)

        print("Finished adding match number: " + matchnum)
        print("Sleeping 30sec now")
        print("=========================================")
        sleep(30)


matches = matchnum_getter("Test")
match_data(matches, "Test")
matches = matchnum_getter("ODI")
match_data(matches, "ODI")


db.commit()

db.close()
