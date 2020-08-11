from bs4 import BeautifulSoup
import requests
import datetime
import re

year = str(datetime.datetime.now().year)

page = requests.get("https://stats.espncricinfo.com/ci/engine/records/team/match_results.html?class=1;id=" + year +
                    ";type=year")

soup = BeautifulSoup(page.content, 'html.parser')

results = soup.find_all("a", href=re.compile("ci/engine/match/"))
pure_matches = []

with open("addedmatches.txt", "r") as f:
    pure_matches = f.read()

with open("addedmatches.txt", "a") as f:
    for matchnum in results:
        name = str(matchnum.get('href')).replace("/ci/engine/match/", "")
        name = name.replace(".html", "")

        if name not in pure_matches:
            print(name, file=f)