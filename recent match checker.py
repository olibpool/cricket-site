from bs4 import BeautifulSoup
import requests
import datetime
import re

year = str(datetime.datetime.now().year)
formats = ["Test", "ODI"]

def pagegetter(format, year):
    return requests.get("https://stats.espncricinfo.com/ci/engine/records/team/match_results.html?class=" +
                        str(format) + ";id=" + year + ";type=year")

def match_adder(format, page):
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all("a", href=re.compile("ci/engine/match/"))

    with open("addedmatches" + formats[format - 1] + ".txt", "r") as f:
        pure_matches = f.read()

    with open("addedmatches" + formats[format - 1] + ".txt", "a") as f:
        for matchnum in results:
            name = str(matchnum.get('href')).replace("/ci/engine/match/", "")
            name = name.replace(".html", "")

            if name not in pure_matches:
                print(name, file=f)


page = pagegetter(1, year)
match_adder(1, page)

page = pagegetter(2, year)
match_adder(2, page)


# Date checking code:
"""
dates = []
for i in results:
    text = i.get_text()
    counter = 0
    word  = ""
    for index, letter in enumerate(text):
        if letter == "\n":
            counter += 1
        if counter == 6 and letter != "\n":
            if letter != " ":
                word += str(letter)
            else:
                dates.append(word)
                word = ""
print(dates)
"""