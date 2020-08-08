from flask import Flask, request, render_template
import sqlite3

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

        # Check what the user wants to analyse:
        batorbowl = request.form.get("batorbowl")
        if batorbowl == "bat":
            which = 'InningsBattedFlag=1'
        elif batorbowl == "bowl":
            which = 'InningsBowledFlag=1'
        else:
            which = 'InningsBattedFlag=1 AND InningsBowledFlag=1'

        TestorODI = request.form.get("TestorODI")

        print(TestorODI)

        # Connect to the stats database:

        return render_template('index.html')
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
