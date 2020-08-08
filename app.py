from flask import Flask, request, render_template
import sqlite3
import codecs
import sys

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


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        # Take the name that the user inputted:
        name = request.form.get("name")
        name = "'" + name + "'"

        # Check what the user wants to analyse:
        batorbowl = request.form.get("batorbowl")
        if batorbowl == "bat":
            which = 'InningsBattedFlag=1'
        elif batorbowl == "bowl":
            which = 'InningsBowledFlag=1'
        else:
            which = '(InningsBattedFlag=1 OR InningsBowledFlag=1)'

        TestorODI = request.form.get("TestorODI")

        # Connect to the stats database:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        # Get last matchdate:
        c.execute("SELECT InningsDate FROM " + quote_identifier(TestorODI).strip('\"') + " ORDER BY InningsDate DESC LIMIT 1")
        last = c.fetchone()[0]
        
        # Get data from stats.db
        data = c.execute("SELECT * FROM " + quote_identifier(TestorODI).strip('\"') + " WHERE (" + quote_identifier(which).strip('\"') + " AND InningsPlayer=" + quote_identifier(name).strip('\"') + ")")

        if data == "":
            print("There is no player in the database called " + str(player))
            print("Make sure you use the format used by cricinfo (e.g BA Stokes).")

        # Initialising variables
        batmatchstats = [('Match Number', 'Match Date', 'Runs Scored', 'Number of Dismissals')]
        bowlmatchstats = [('Match Number', 'Match Date', 'Runs Conceeded', 'Wickets')]
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
        i = 0

        # Generate player data in list
        for rowdata in data:
            if rowdata[13] != date or lastrow == True:
                if firstrow != True:
                    
                    totruns += runs
                    totouts += outs
                    totbowlruns += bowlruns
                    totwickets += wickets
                    
                    if totouts != 0:
                        cumulativebat.append(totruns/totouts)
                    else:
                        cumulativebat.append(0)
                    if totwickets != 0:
                        cumulativebowl.append(totbowlruns/totwickets)
                    else:
                        cumulativebowl.append(0)
                    if cumulativebat[match - 1] > graphmax:
                        graphmax = cumulativebat[match - 1]
                    if cumulativebowl[match - 1] > graphmax:
                        graphmax = cumulativebowl[match - 1]

                    batmatchstats.append((match, date, runs, outs))
                    bowlmatchstats.append((match, date, bowlruns, wickets))
                    
                    match += 1
                    runs = 0
                    outs = 0
                    bowlruns = 0
                    wickets = 0

                else:
                    firstrow = False

                date = rowdata[13]

                

            if rowdata[4] == 1:
                runs += int(rowdata[2])
                if int(rowdata[5]) != 1:
                    outs += 1
            else:
                if rowdata[19] == 1:
                    bowlruns += int(rowdata[21])
                    wickets += int(rowdata[22])

        # Add last match to data:
        totruns += runs
        totouts += outs
        totbowlruns += bowlruns
        totwickets += wickets
        
        if totouts != 0:
            cumulativebat.append(totruns/totouts)
        else:
            cumulativebat.append(0)
        if totwickets != 0:
            cumulativebowl.append(totbowlruns/totwickets)
        else:
            cumulativebowl.append(0)
        if cumulativebat[match - 1] > graphmax:
            graphmax = cumulativebat[match - 1]
        if cumulativebowl[match - 1] > graphmax:
            graphmax = cumulativebowl[match - 1]

        batmatchstats.append((match, date, runs, outs))
        bowlmatchstats.append((match, date, bowlruns, wickets))

        if batyes == True:
            plt.plot(range(1, match), cumulativebat, label = "Batting average")
        if bowlyes == True:
            plt.plot(range(1, match), cumulativebowl, label = "Bowling average")
        plt.axis([0,match,0,graphmax + 5])
        plt.xlabel('Number of matches')
        plt.ylabel('Average')
        plt.title(str(matchtype) + ' averages for ' + str(player))
        plt.legend()
        plt.show()

        print(batmatchstats)
        return render_template('index.html')
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
