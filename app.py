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

app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
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

        print(name)

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
                '\"') + " AND InningsPlayer=" + quote_identifier(name).strip('\"') + ")")

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

        return render_template("output.html", graph=pngImageB64String,
                               bowlmatchstats=bowlmatchstats, batmatchstats=batmatchstats, which=batorbowl,
                               batavg=round(cumulativebat[-1],2), bowlavg=round(cumulativebowl[-1],2))
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
