from flask import Flask
from flask import request, render_template
import sqlite3
from collections import Counter
from math import pi

import pandas as pd

from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.layouts import gridplot
from bokeh.embed import components


app = Flask(__name__)


def user_index():
    with open("users.txt", 'r', encoding='utf-8') as f:
        id = f.read()
    if id:
        new_id = int(id) + 1
        with open("users.txt", "w", encoding="utf-8") as f:
            f.write(str(new_id))
        return new_id
    else:
        new_id = 1
        with open("users.txt", "w", encoding="utf-8") as f:
            f.write(str(new_id))
        return new_id


@app.route('/')
def index():
    conn = sqlite3.connect('tight.sqlite')
    c = conn.cursor()
    command = 'CREATE TABLE IF NOT EXISTS answers(ID_user INTEGER UNIQUE, lang VARCHAR, age VARCHAR, place VARCHAR, '
    for i in range(1, 46):
        if i != 45:
            command += 'Quest' + str(i) + ' VARCHAR, '
        else:
            command += 'Quest' + str(i) + ' VARCHAR)'
    c.execute(command)
    return render_template('home.html')


@app.route('/quests')
def quests():
    conn = sqlite3.connect('tight.sqlite')
    c = conn.cursor()
    if request.args:
        answers = [user_index()]
        questions_gen = ['lang', 'age', 'place']
        questions_meaning = ["Quest" + str(i) for i in range(1, 46)]
        for i in questions_gen:
            answers.append(request.args[i])
        for i in questions_meaning:
            answers.append(request.args[i])
        c.execute('INSERT OR IGNORE INTO answers(ID_user) VALUES (?)', (str(answers[0])))
        c.execute('UPDATE answers SET lang = "{}" WHERE ID_user = {}'.format(answers[1], answers[0]))
        c.execute('UPDATE answers SET age = "{}" WHERE ID_user = {}'.format(answers[2], answers[0]))
        c.execute('UPDATE answers SET place = "{}" WHERE ID_user = {}'.format(answers[3], answers[0]))
        for i in range(1, 46):
            c.execute('UPDATE answers SET Quest{} = "{}" WHERE ID_user = {}'.format(str(i), answers[i + 3], answers[0]))
        conn.commit()
        return render_template('thanks.html')
    return render_template("quests.html")


@app.route('/stats')
def stats():
    names = ['id пользователя', 'Язык', 'Возраст', 'Место проживания']
    for i in range(1, 46):
        names.append('Вопрос {}'.format(str(i)))
    conn = sqlite3.connect('tight.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM answers")
    answers = c.fetchall()
    answers_cols = []
    len1 = len(names)
    for i in range(len(answers[0])):
        col = []
        for row in answers:
            col.append(row[i])
        answers_cols.append(col)
    return render_template("stats.html", names=names, len1=len1, answers_cols=answers_cols)


def count_items(str1):
    conn = sqlite3.connect('tight.sqlite')
    c = conn.cursor()

    c.execute("SELECT {} FROM answers".format(str1))
    age = c.fetchall()
    age_n = []
    data1 = []
    if str1 == "place" or "lang":
        age = [(i[0].capitalize(),) for i in age]
    for i in age:
        if i[0] not in age_n:
            age_n.append(i[0])
            data1.append(age.count(i))
    return Counter({age_n[i]: data1[i] for i in range(len(age_n))})


def pie_plot(str1):
    x = count_items(str1)
    data = pd.DataFrame.from_dict(dict(x), orient='index').reset_index().rename(index=str, columns={0: 'value',
                                                                                                    'index': str1})
    data['angle'] = data['value'] / sum(x.values()) * 2 * pi
    if len(x) < 3:
        colours = ['#3182bd', '#6baed6', '#9ecae1']
        data['color'] = colours[:len(x)]
    else:
        data['color'] = Category20c[len(x)]
    p = figure(plot_height=350, title=str1.capitalize(), toolbar_location=None,
               tools="hover", tooltips="@{}: @value".format(str1))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend=str1, source=data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None
    return p


def graphs():
    p = pie_plot('age')
    p1 = pie_plot('place')
    p2 = pie_plot('lang')
    p0 = gridplot([p, p1], [p2, None])
    script, div = components(p0)
    return script, div


@app.route('/stats/users')
def stats_users():
    html = graphs()
    script = html[0]
    div = html[1]
    return render_template('stats_users.html', script=script, div=div)


if __name__ == '__main__':
    app.run(debug=True)