# cricket-site

This Flask web-app takes requests from the user to select the name of a cricketer, the format to analyse and whether to look at batting and bowling. 

It then executes a SQLite query on the stats.db database to select the necessary rows, formats the infomation into a python-usale list, then sends this list to 
plotly.js via a JSON-string. 

This JSON string is then turned into an interactive graph on the output page and printed out alongside an innings by innings summary of the player's career.

There is also a rolling average analyser on the /rolling route, which works in much the same way.
