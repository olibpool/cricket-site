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
        

        # Connect to the stats database:
        conn = sqlite3.connect("stats.db")
        c = conn.cursor()

        c.execute("SELECT :batorbowl")



    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
