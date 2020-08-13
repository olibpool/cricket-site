import base64
import codecs
import io
import sqlite3
import matplotlib.pyplot as plt
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
        if batorbowl == "Batting":
            which = 'InningsBattedFlag=1'
        elif batorbowl == "Bowling":
            which = 'InningsBowledFlag=1'
        else:
            which = '(InningsBattedFlag=1 OR InningsBowledFlag=1)'

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
                  ".\nMake sure you use the standard format for scorecards (e.g BA Stokes)."

        if check is None:
            flash(msg)
            return redirect("/")

        last = check[0]

        # Get data from stats.db
        data = c.execute(
            "SELECT DISTINCT * FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE (" + quote_identifier(
                which).strip(
                '\"') + " AND InningsPlayer=" + quote_identifier(name).strip('\"') + ") ORDER BY InningsDate")

        # Initialising variables
        batmatchstats = [('Match Number', 'Match Date', 'Opposition', 'Ground', 'Runs Scored', 'Number of Dismissals')]
        bowlmatchstats = [('Match Number', 'Match Date', 'Opposition', 'Ground', 'Runs Conceded', 'Wickets')]
        cumulativebat = []
        cumulativebowl = []
        graphmax = 0
        match = 1
        runs = 0
        bowlruns = 0
        outs = 0
        wickets = 0
        totruns = 0
        totouts = 0
        totbowlruns = 0
        totwickets = 0
        firstrow = True
        lastrow = False
        date = "blah"
        opp = "blah"
        ground = "blah"
        i = 0

        # Generate player data in list
        for rowdata in data:
            if rowdata[13] != date or lastrow:
                if not firstrow:

                    totruns += runs
                    totouts += outs
                    totbowlruns += bowlruns
                    totwickets += wickets

                    if totouts != 0:
                        cumulativebat.append(totruns / totouts)
                    else:
                        cumulativebat.append(0)
                    if totwickets != 0:
                        cumulativebowl.append(totbowlruns / totwickets)
                    else:
                        cumulativebowl.append(0)
                    if cumulativebat[match - 1] > graphmax:
                        graphmax = cumulativebat[match - 1]
                    if cumulativebowl[match - 1] > graphmax:
                        graphmax = cumulativebowl[match - 1]

                    batmatchstats.append((match, date, opp, ground, runs, outs))
                    bowlmatchstats.append((match, date, opp, ground, bowlruns, wickets))

                    match += 1
                    runs = 0
                    outs = 0
                    bowlruns = 0
                    wickets = 0

                else:
                    firstrow = False

                opp = rowdata[11]
                ground = rowdata[12]
                date = rowdata[13]

            if rowdata[4] == 1:
                runs += int(rowdata[2])
                if int(rowdata[5]) != 1:
                    outs += 1
            elif rowdata[19] == 1:
                bowlruns += int(rowdata[21])
                wickets += int(rowdata[22])

        # Add last match to data:
        totruns += runs
        totouts += outs
        totbowlruns += bowlruns
        totwickets += wickets

        if totouts != 0:
            cumulativebat.append(totruns / totouts)
        else:
            cumulativebat.append(0)
        if totwickets != 0:
            cumulativebowl.append(totbowlruns / totwickets)
        else:
            cumulativebowl.append(0)
        if cumulativebat[match - 1] > graphmax:
            graphmax = cumulativebat[match - 1]
        if cumulativebowl[match - 1] > graphmax:
            graphmax = cumulativebowl[match - 1]

        batmatchstats.append((match, date, opp, ground, runs, outs))
        bowlmatchstats.append((match, date, opp, ground, bowlruns, wickets))

        # Plotting the data
        plt.style.use('Solarize_Light2')
        fig = plt.figure()
        ax = fig.add_subplot()
        if batorbowl in ["Batting", "Both"]:
            ax.plot(range(1, match + 1), cumulativebat, label="Batting average")
        if batorbowl in ["Bowling", "Both"]:
            ax.plot(range(1, match + 1), cumulativebowl, label="Bowling average")
        ax.set_xlim(0, match + 2)
        ax.set_ylim(0, graphmax + 5)
        ax.set_xlabel('Number of matches')
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

        c.close()

        return render_template("output.html", graph=pngImageB64String,
                               bowlmatchstats=bowlmatchstats, batmatchstats=batmatchstats, which=batorbowl,
                               batavg=round(cumulativebat[-1],2), bowlavg=round(cumulativebowl[-1],2))
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
        if batorbowl == "Batting":
            which = 'InningsBattedFlag=1'
        elif batorbowl == "Bowling":
            which = 'InningsBowledFlag=1'
        else:
            which = '(InningsBattedFlag=1 OR InningsBowledFlag=1)'

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
            msg = name + "has only played " + str(numofgames) + TestorODI + " games, choose a smaller interval."
            flash(msg)
            return redirect("/rolling")

        last = check[0]

        # Get data from stats.db
        data = c.execute(
            "SELECT DISTINCT * FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE (" + quote_identifier(
                which).strip(
                '\"') + " AND InningsPlayer=" + quote_identifier(name).strip('\"') + ") ORDER BY InningsDate")

        # Initialising variables
        batmatchstats = [('Match Number', 'Match Date', 'Opposition', 'Ground', 'Runs Scored', 'Number of Dismissals')]
        bowlmatchstats = [('Match Number', 'Match Date', 'Opposition', 'Ground', 'Runs Conceded', 'Wickets')]
        cumulativebat = []
        cumulativebowl = []
        rollingbat = []
        rollingbowl = []
        graphmax = 0
        rollgraphmax = 0
        match = 1
        runs = 0
        bowlruns = 0
        outs = 0
        wickets = 0
        totruns = 0
        totouts = 0
        totbowlruns = 0
        totwickets = 0
        firstrow = True
        lastrow = False
        date = "blah"
        opp = "blah"
        ground = "blah"
        i = 0

        # Generate player data in list
        for rowdata in data:
            if rowdata[13] != date or lastrow:
                if not firstrow:

                    totruns += runs
                    totouts += outs
                    totbowlruns += bowlruns
                    totwickets += wickets

                    if totouts != 0:
                        cumulativebat.append(totruns / totouts)
                    else:
                        cumulativebat.append(0)
                    if totwickets != 0:
                        cumulativebowl.append(totbowlruns / totwickets)
                    else:
                        cumulativebowl.append(0)
                    if cumulativebat[match - 1] > graphmax:
                        graphmax = cumulativebat[match - 1]
                    if cumulativebowl[match - 1] > graphmax:
                        graphmax = cumulativebowl[match - 1]

                    batmatchstats.append((match, date, opp, ground, runs, outs))
                    bowlmatchstats.append((match, date, opp, ground, bowlruns, wickets))

                    match += 1
                    runs = 0
                    outs = 0
                    bowlruns = 0
                    wickets = 0

                else:
                    firstrow = False

                opp = rowdata[11]
                ground = rowdata[12]
                date = rowdata[13]

            if rowdata[4] == 1:
                runs += int(rowdata[2])
                if int(rowdata[5]) != 1:
                    outs += 1
            elif rowdata[19] == 1:
                bowlruns += int(rowdata[21])
                wickets += int(rowdata[22])

        # Add last match to data:
        totruns += runs
        totouts += outs
        totbowlruns += bowlruns
        totwickets += wickets

        if totouts != 0:
            cumulativebat.append(totruns / totouts)
        else:
            cumulativebat.append(0)
        if totwickets != 0:
            cumulativebowl.append(totbowlruns / totwickets)
        else:
            cumulativebowl.append(0)
        if cumulativebat[match - 1] > graphmax:
            graphmax = cumulativebat[match - 1]
        if cumulativebowl[match - 1] > graphmax:
            graphmax = cumulativebowl[match - 1]

        batmatchstats.append((match, date, opp, ground, runs, outs))
        bowlmatchstats.append((match, date, opp, ground, bowlruns, wickets))

        for i in range(1, len(batmatchstats) + 1):
            if i > period:
                rollruns = 0
                rollouts = 0
                rollbowlruns = 0
                rollwickets = 0

                for j in range(i - period, i):
                    rollruns += int(batmatchstats[j][4])
                    rollouts += int(batmatchstats[j][5])
                    rollbowlruns += int(bowlmatchstats[j][4])
                    rollwickets += int(bowlmatchstats[j][5])

                # Creating rolling batting average
                if rollouts != 0:
                    rollingbat.append(rollruns / rollouts)
                else:
                    rollingbat.append(0)

                # Creating rolling bowling average
                if rollwickets != 0:
                    rollingbowl.append(rollbowlruns / rollwickets)
                else:
                    rollingbowl.append(0)

                # Sort out graph range
                if batorbowl in ['Batting', 'Both']:
                    if rollingbat[-1] > rollgraphmax:
                        rollgraphmax = rollingbat[-1]
                if batorbowl in ['Bowling', 'Both']:
                    if rollingbowl[-1] > rollgraphmax:
                        rollgraphmax = rollingbowl[-1]

        # Plotting the data
        plt.style.use('Solarize_Light2')
        fig = plt.figure()
        ax = fig.add_subplot()
        if batorbowl in ["Batting", "Both"]:
            ax.plot(range(period, match + 1), rollingbat, label="Batting average")
        if batorbowl in ["Bowling", "Both"]:
            ax.plot(range(period, match + 1), rollingbowl, label="Bowling average")
        ax.set_xlim(period, match + 2)
        ax.set_ylim(0, rollgraphmax + 5)
        ax.set_xlabel('Number of matches')
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

        return render_template("outputrolling.html", graph=pngImageB64String,
                               bowlmatchstats=bowlmatchstats, batmatchstats=batmatchstats, which=batorbowl,
                               batavg=round(cumulativebat[-1],2), bowlavg=round(cumulativebowl[-1],2), period=period)
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
