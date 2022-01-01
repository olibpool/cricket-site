import base64
import codecs
import io
import sqlite3
import matplotlib.pyplot as plt
import pandas
from flask import Flask, request, render_template, flash, redirect
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


def quote_identifier(s, errors="strict"):
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""


app: Flask = Flask(__name__)
app.config['SECRET_KEY'] = 'p2fAJzrORrIWVyRE3kI0eA'


@app.route('/', methods=['GET', 'POST'])
def main_page():
    if request.method == 'POST':
        # Take the name that the user inputted:
        nametest = request.form.get("name")
        name = "'" + nametest + "'"

        # Check what the user wants to analyse:
        batorbowl = request.form.get("batorbowl")
        TestorODI = request.form.get("TestorODI")

        # Connect to the stats database:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        # Get last matchdate:
        c.execute(
            "SELECT InningsDate FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE InningsPlayer=" +
            quote_identifier(name).strip('\"') + " ORDER BY InningsDate DESC LIMIT 1")

        check = c.fetchone()

        # Checking player exists
        if nametest == '':
            msg = "Make sure to put in a player's name before clicking analyse!\n"
        else:
            msg = "There is no player in the database called " + str(name) + \
                  ".\nMake sure you use the standard format for scorecards (e.g 'Joe Root')."

        if check is None:
            flash(msg)
            return redirect("/")

        # Get data from stats.db
        data = c.execute(
            "SELECT * FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE InningsPlayer="
            + quote_identifier(name).strip('\"') + " ORDER BY InningsDate")

        # Initialising variables
        batmatchstats = [('Innings Number', 'Match Date', 'Opposition', 'Ground', 'Runs Scored')]
        bowlmatchstats = [('Innings Number', 'Match Date', 'Opposition', 'Ground', 'Runs Conceded', 'Wickets')]
        cumulativebat = []
        cumulativebowl = []
        graphmax = 0
        batins = 0
        bowlins = 0
        totruns = 0
        totouts = 0
        totbowlruns = 0
        totwickets = 0

        # Generate player data in list
        for rowdata in data:
            opp = rowdata[11]
            ground = rowdata[12]
            date = rowdata[13]

            if rowdata[4] == 1:  # inningsbattedflag
                batins += 1

                runs = rowdata[1]
                totruns += int(rowdata[2])

                if rowdata[5] == 0:
                    totouts += 1

                if totouts != 0:
                    cumulativebat.append(totruns / totouts)
                else:
                    cumulativebat.append(0)

                if cumulativebat[batins - 1] > graphmax:
                    graphmax = cumulativebat[batins - 1]

                batmatchstats.append((batins, date, opp, ground, runs))

            if rowdata[19] == 1:  # inningsbowledflag
                bowlins += 1
                bowlruns = int(rowdata[21])
                totbowlruns += bowlruns

                wickets = int(rowdata[22])
                totwickets += wickets

                if totwickets != 0:
                    cumulativebowl.append(totbowlruns / totwickets)
                else:
                    cumulativebowl.append(0)

                if cumulativebowl[bowlins - 1] > graphmax:
                    graphmax = cumulativebowl[bowlins - 1]

                bowlmatchstats.append((bowlins, date, opp, ground, bowlruns, wickets))

        dates = [x[1] for x in batmatchstats + bowlmatchstats]
        matches = len(set(dates)) - 1

        # Plotting the data
        plt.style.use('Solarize_Light2')
        fig = plt.figure()
        ax = fig.add_subplot()
        if batorbowl in ["Batting", "Both"]:
            ax.plot(range(1, batins + 1), cumulativebat, label="Batting average")
        if batorbowl in ["Bowling", "Both"]:
            ax.plot(range(1, bowlins + 1), cumulativebowl, label="Bowling average")
        ax.set_xlim(1, max(batins, bowlins) + 0.5)
        ax.set_ylim(0, graphmax + 5)
        ax.set_xlabel('Number of innings')
        ax.set_ylabel('Average')
        ax.set_title(str(TestorODI) + ' averages for ' + str(name))
        ax.legend()
        ax.grid(alpha=100)

        # Convert plot to PNG image
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)

        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')

        # To keep functionality if only chosing batting or bowling.
        if not cumulativebat:
            cumulativebat = [0]
        if not cumulativebowl:
            cumulativebowl = [0]

        c.close()

        return render_template("output.html", graph=pngImageB64String,
                               bowlmatchstats=bowlmatchstats, batmatchstats=batmatchstats, which=batorbowl,
                               batavg=round(cumulativebat[-1], 3), bowlavg=round(cumulativebowl[-1], 3),
                               matches=matches)
    else:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        c.execute("SELECT DISTINCT InningsPlayer FROM Test")

        namesstart = c.fetchall()
        names = []

        for name in namesstart:
            names.append(name[0])

        c.close()
        return render_template('index.html', names=names)


@app.route('/rolling', methods=['GET', 'POST'])
def rolling_page():
    if request.method == 'POST':
        # Take the name that the user inputted:
        nametest = request.form.get("name")
        name = "'" + nametest + "'"

        # Check what the user wants to analyse:
        batorbowl = request.form.get("batorbowl")
        TestorODI = request.form.get("TestorODI")

        period = request.form.get("period")

        # Connect to the stats database:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        # Get last matchdate:
        c.execute(
            "SELECT InningsDate FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE InningsPlayer=" +
            quote_identifier(name).strip('\"') + " ORDER BY InningsDate DESC LIMIT 1")

        check = c.fetchone()

        # Checking player exists
        if nametest == '':
            msg = "Make sure to put in a player's name before clicking analyse!\n"
        else:
            msg = "There is no player in the database called " + str(name) + \
                  ".\nMake sure you use the standard format for scorecards (e.g BA Stokes)."
        if check is None:
            flash(msg)
            return redirect("/rolling")

        c.execute("SELECT DISTINCT COUNT(DISTINCT InningsDate) FROM " +
                  quote_identifier(TestorODI).strip('\"') + " WHERE InningsPlayer="
                  + quote_identifier(name).strip('\"'))

        numofgames = c.fetchone()[0]

        if period == '':
            flash("Make sure to write in a period to analyse over!")
            return redirect("/rolling")

        period = int(period)

        if period < 1:
            flash("Make sure to write a positive integer in the rolling average box!")
            return redirect("/rolling")

        if int(numofgames) < period:
            msg = name + " has only played " + str(numofgames) + " " + \
                  TestorODI + " games, choose a smaller interval."
            flash(msg)
            return redirect("/rolling")

        last = check[0]

        # Get data from stats.db
        data = c.execute(
            "SELECT DISTINCT * FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE InningsPlayer="
            + quote_identifier(name).strip('\"') + " ORDER BY InningsDate")

        # Initialising variables
        batmatchstats = [('Innings Number', 'Match Date', 'Opposition', 'Ground', 'Runs Scored', 'Not Out')]
        bowlmatchstats = [('Innings Number', 'Match Date', 'Opposition', 'Ground', 'Runs Conceded', 'Wickets')]
        cumulativebat = []
        cumulativebowl = []
        rollingbat = []
        rollingbowl = []
        graphmax = 0
        rollgraphmax = 0
        match = 1
        totruns = 0
        totouts = 0
        totbowlruns = 0
        totwickets = 0
        batins = 0
        bowlins = 0

        # Generate player data in list
        for rowdata in data:
            opp = rowdata[11]
            ground = rowdata[12]
            date = rowdata[13]

            if rowdata[4] == 1:  # inningsbattedflag
                batins += 1

                runs = rowdata[1]
                totruns += int(rowdata[2])

                if rowdata[5] == 0:
                    totouts += 1
                    out = 1
                else:
                    out = 0

                if totouts != 0:
                    cumulativebat.append(totruns / totouts)
                else:
                    cumulativebat.append(0)

                if cumulativebat[batins - 1] > graphmax:
                    graphmax = cumulativebat[batins - 1]

                batmatchstats.append((batins, date, opp, ground, runs, out))

            if rowdata[19] == 1:  # inningsbowledflag
                bowlins += 1
                bowlruns = int(rowdata[21])
                totbowlruns += bowlruns

                wickets = int(rowdata[22])
                totwickets += wickets

                if totwickets != 0:
                    cumulativebowl.append(totbowlruns / totwickets)
                else:
                    cumulativebowl.append(0)

                if cumulativebowl[bowlins - 1] > graphmax:
                    graphmax = cumulativebowl[bowlins - 1]

                bowlmatchstats.append((bowlins, date, opp, ground, bowlruns, wickets))

        dates = [x[1] for x in batmatchstats + bowlmatchstats]
        matches = len(set(dates)) - 1

        if batorbowl in ['Batting', 'Both']:
            for i in range(1, batins + 1):
                if i > period:
                    rollruns = 0
                    rollouts = 0

                    for j in range(i - period, i):
                        rollruns += int(batmatchstats[j][4].split("*")[0])
                        rollouts += int(batmatchstats[j][5])

                    # Creating rolling batting average
                    if rollouts != 0:
                        rollingbat.append(rollruns / rollouts)
                    else:
                        rollingbat.append(0)

                    # Sort out graph range
                    if rollingbat[-1] > rollgraphmax:
                        rollgraphmax = rollingbat[-1]

        if batorbowl in ['Bowling', 'Both']:
            for i in range(1, bowlins + 1):
                if i > period:
                    rollbowlruns = 0
                    rollwickets = 0

                    for j in range(i - period, i):
                        rollbowlruns += int(bowlmatchstats[j][4])
                        rollwickets += int(bowlmatchstats[j][5])

                    # Creating rolling bowling average
                    if rollwickets != 0:
                        rollingbowl.append(rollbowlruns / rollwickets)
                    else:
                        rollingbowl.append(0)

                    # Sort out graph range
                    if rollingbowl[-1] > rollgraphmax:
                        rollgraphmax = rollingbowl[-1]

        # Plotting the data
        plt.style.use('Solarize_Light2')
        fig = plt.figure()
        ax = fig.add_subplot()
        if batorbowl in ["Batting", "Both"]:
            ax.plot(range(period, batins), rollingbat, label="Batting average")
        if batorbowl in ["Bowling", "Both"]:
            ax.plot(range(period, bowlins), rollingbowl, label="Bowling average")
        ax.set_xlim(period, max(batins, bowlins) + 0.5)
        ax.set_ylim(0, rollgraphmax + 5)
        ax.set_xlabel('Number of innings')
        ax.set_ylabel('Average')
        ax.set_title("Rolling " + str(TestorODI) + ' averages for ' + str(name) + " period: " + str(period))
        ax.legend()
        ax.grid(alpha=100)

        # Convert plot to PNG image
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)

        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')

        # To keep functionality if only chosing batting or bowling.
        if cumulativebat == []:
            cumulativebat = [0]
        if cumulativebowl == []:
            cumulativebowl = [0]

        return render_template("outputrolling.html", graph=pngImageB64String,
                               bowlmatchstats=bowlmatchstats, batmatchstats=batmatchstats, which=batorbowl,
                               batavg=round(cumulativebat[-1], 3), bowlavg=round(cumulativebowl[-1], 3), period=period,
                               matches=matches)
    else:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        c.execute("SELECT DISTINCT InningsPlayer FROM Test")

        namesstart = c.fetchall()
        names = []

        for name in namesstart:
            names.append(name[0])

        c.close()
        return render_template('rolling.html', names=names)


if __name__ == '__main__':
    app.run()
