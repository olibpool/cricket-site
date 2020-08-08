from flask import Flask

app = Flask(__name__)

app.config['ENV'] = "development"
app.config['DEBUG'] = 1


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
