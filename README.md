# ScoreBoard
This simple web application provides a scoreboard. Users can upload their source code onto this web application. And then it compiles and runs uploaded source code. When the program is finished, it verifies the output of the program. If the result is accurate, it's going to record the elapsed time of the program in the scoreboard.

### HOW TO INSTALL & RUN
To run this application, some programs are required as follows.
- Python
- Flask
- SQLite3

First, download this source code
```
$ git clone https://github.com/jungsikchoi/ScoreBoard.git
```

Second, make preparations
```
$ cd ScoreBoard
$ sudo apt-get install python-virtualenv
$ virtualenv venv
$ . venv/bin/activate
(venv)$ pip install Flask
```

Finally, run
```
(venv)$ python score_board.py
```
