import ast
import random
from sqlite3.dbapi2 import Cursor
import requests
from bs4 import BeautifulSoup
import sqlite3
from time import sleep
import dateparser
import os.path

# TODO Add comments

# TODO add odi num 64473, 66013 manually
# test 1104483 appears to have been deleted?
# test https://stats.espncricinfo.com/ci/engine/match/64095.html needs to be added manually for some reason.

path_to_dir = os.path.dirname(__file__)

db = sqlite3.connect(path_to_dir + "/stats.db")
c: Cursor = db.cursor()


def stats(matchformat, type, pagenum):
    # Creates a tables of the statistics for the batsmen/ bowlers.

    page = requests.get(
        "https://stats.espncricinfo.com/ci/engine/stats/index.html?class=" + str(matchformat) +
        ";filter=advanced;orderby=start;page=" + str(pagenum) +
        ";size=200;template=results;type=" + type + ";view=innings")

    soup = BeautifulSoup(page.content, 'html.parser')

    # these tables contain stats for each bowler and batsmen
    div = soup.find("div", class_="pnl650M")
    table = div.find_all("tr", class_="data1")

    stats = []

    for counter, row in enumerate(table):
        stats.append([])

        rowdata = row.find_all("td")

        for i, row in enumerate(rowdata):
            if i == 0:
                name = row.text.split("(")[0][:-1]
                country = row.text.split("(")[1]
                country = country.split(")")[0]
                stats[counter].append(name)
                stats[counter].append(country)
            elif i != 8 and i != 12:
                stats[counter].append(row.text)

    return stats


def match_data_importer(matchformat, type):
    # This function creates a list of matches that need to be added to the database

    with open(path_to_dir + "/data/compPageNumber" + str(matchformat) + type + ".txt", "r") as f:
        compPages = int(f.read())

    page = requests.get(
        "https://stats.espncricinfo.com/ci/engine/stats/index.html?class=" + str(matchformat) +
        ";filter=advanced;orderby=start;page=1;"
        "size=200;template=results;type=" + type + ";view=innings")

    soup = BeautifulSoup(page.content, 'html.parser')
    div = soup.find("div", class_="pnl650M")
    row = div.find_all("tr", class_="data2")
    pages = row[2].find("td")
    newestPageNum = int(pages.find_all("b")[1].text)

    if matchformat == 1:
        matchformatName = "Test"
    else:
        matchformatName = "ODI"

    print()
    print(matchformatName + " " + type)
    print("Newest Page Num = " + str(newestPageNum))
    print()

    with open(path_to_dir + "/data/lastData" + str(matchformat) + type + ".txt", 'r') as filetoread:
        lastData = ast.literal_eval(filetoread.read())

    for pagenum in range(compPages, newestPageNum + 1):
        print("Now adding page number: " + str(pagenum))
        print()

        page = stats(matchformat, type, pagenum)

        for row in page:
            if row not in lastData:
                if row[2] not in ['TDNB', 'DNB', 'absent', 'sub']:  # checks for did not bats/bowls
                    if type == "batting":
                        # batting
                        # row [name, not out flag, runs, faced, mins, 4s, 6s, strike rate]
                        name = row[0]
                        country = row[1]
                        runs = row[2]
                        if "*" in runs:
                            notout = 1
                        else:
                            notout = 0

                        runsnum = int(runs.split("*")[0])

                        mins = row[3]
                        faced = row[4]
                        fours = row[5]
                        sixes = row[6]
                        sr = row[7]
                        inns = row[8]
                        opp = row[9]
                        ground = row[10]
                        date = dateparser.parse(row[11])
                        date = str(date.date())

                        if runsnum < 50:
                            row50 = 0
                            row100 = 0
                            buck = "0-49"
                        elif 50 <= runsnum < 100:
                            row50 = 1
                            row100 = 0
                            buck = "50-99"
                        elif 100 <= runsnum < 150:
                            row50 = 0
                            row100 = 1
                            buck = "100-149"
                        elif 150 <= runsnum < 200:
                            row50 = 0
                            row100 = 1
                            buck = "150-199"
                        else:
                            row50 = 0
                            row100 = 1
                            buck = "200+"

                        query = "INSERT INTO {} (InningsPlayer, InningsRunsScored, InningsRunsScoredNum," \
                                " InningsMinutesBatted, InningsBattedFlag, InningsNotOutFlag, InningsBallsFaced, " \
                                "InningsBoundaryFours, InningsBoundarySixes, InningsBattingStrikeRate, InningsNumber," \
                                " Opposition, Ground, InningsDate, Country, '50s', '100s', 'InningsRunsScoredBuckets')" \
                                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?)".format(matchformatName)

                        c.execute(query,
                                  [name, runs, runsnum, mins, 1, notout, faced, fours,
                                   sixes, sr, inns, opp, ground, date, country, row50, row100, buck])
                    else:
                        # bowling
                        # row [name, overs, maidens, runs, wickets, econ, wides, no balls]

                        name = row[0]
                        country = row[1]
                        overs = row[2]
                        maidens = row[4]
                        conceded = row[5]
                        wickets = int(row[6])
                        econ = row[7]
                        inns = row[8]
                        opp = row[9]
                        ground = row[10]
                        date = dateparser.parse(row[11])
                        date = str(date.date())

                        if wickets < 5:
                            wick4 = 1
                            wick5 = 0
                            wick10 = 0
                            buck = "0-4"
                        elif 5 <= wickets < 10:
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
                                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(matchformatName)

                        c.execute(query, [name, inns, opp, ground, date, country, overs, 1, maidens, conceded, wickets,
                                          wick4, wick5, wick10, buck, econ])

        if pagenum == newestPageNum:
            with open(path_to_dir + "/data/lastData" + str(matchformat) + type + ".txt", 'w') as filetowrite:
                filetowrite.write(str(page))

        db.commit()

        print("Finished adding page number: " + str(pagenum))
        sleeptime = random.uniform(1, 3)  # as to not overload requests and get banned
        print("Sleeping " + str(sleeptime) + " now")
        print("=========================================")
        sleep(sleeptime)

        with open(path_to_dir + "/data/compPageNumber" + str(matchformat) + type + ".txt", 'w') as filetowrite:
            filetowrite.write(str(pagenum))


match_data_importer(1, 'batting')
match_data_importer(1, 'bowling')
match_data_importer(2, 'batting')
match_data_importer(2, 'bowling')

# Remove duplicate rows
# CREATE TABLE temp AS SELECT DISTINCT * FROM Test;
# ALTER TABLE Test RENAME TO junk;
# ALTER TABLE temp RENAME TO Test;
# DROP TABLE junk;

db.close()
