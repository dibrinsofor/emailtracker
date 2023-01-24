from flask import Flask, render_template, request, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import pandas
from imapencoding import login_mail_client, get_mail
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import count_nonzero, min, max, arange
import json
import plotly
import plotly.express as px
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emailtracker.db'
app.debug = True

db = SQLAlchemy(app)

# limit scan to x number of emails for performance, 
# give option increase number. is date a better quantifier?
# ---
# consider storing the number of emails scanned and maybe some of the other data we'd need for results.html upfront
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    results = db.Column(db.String) # contents of the generated .txt file.
    email = db.Column(db.String(40)) # maybe some domains recieve more unecrypted mails
    emails_scanned = db.Column(db.Integer)
    links_found = db.Column(db.Integer)
    createdAt = db.Column(db.DateTime, default=datetime)

    def __repr__(self):
        return '<email %r>' % self.createdAt

@app.route("/home")
@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        email_address = request.form.get('email')
        password = request.form.get('password')

        mail = login_mail_client(email_address, password)
        email_scanned, links_found = get_mail(mail)

        # if request.headers.get('total-emails-scanned'):
        #     email_scanned += request.headers.get('total-emails-scanned')
        # if request.headers.get('all-links-found'):
        #     links_found += request.headers.get('all-links-found')
            
        unsecureJSON = unsecure_plot()
        secureJSON = secure_plot()
        totalJSON = total_plot()

        resp = Response(render_template("results.html", email_scanned=email_scanned, links_found=links_found, unsecureJSON=unsecureJSON, secureJSON=secureJSON, totalJSON=totalJSON))
        
        return resp 
    else:
        return render_template("index.html") 

# not exposed. check if jwt exists or redirect back to index
@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/download/<path:filename>")
def downloadFile(filename):
    # custom filename in results dir passed here
    path = "/" + filename
    return send_file(path, as_attachment=True)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/pubs")
def pubs():
    return render_template("pubs.html")

def sanitize(security_level):
    # TODO take type as argument. Secure or Unsecure
    results = defaultdict(list)

    csv = pandas.read_csv(r'results_data.csv')

    companies = csv['Tracking Service'].unique()
    years = csv['Year'].unique() 

    if len(years) < 5:
        csv['Date'] = csv['Month'].astype(str) +" "+ csv['Year'].astype(str)
        years = csv['Date'].unique()
        results["Years"].extend(years)
    else:
        results["Years"].extend(years)

    for company in companies:
        count = 0
        while len(years) > count:
            print(years[count])
            if type(years[count]) == str:
                company_df = csv[(csv['Tracking Service'] == company) & (csv['Date'] == years[count])]
            elif type(years[count]) == int:
                company_df = csv[(csv['Tracking Service'] == company) & (csv['Year'] == years[count])]

            freq = count_nonzero(company_df[security_level])
            results[company].append(freq)
            count += 1
    
    return results, years

def unsecure_plot():
    csv_results, years = sanitize('Unsecure')
    
    df = pandas.DataFrame.from_dict(csv_results)
    top_5 = df.drop(['Years'], axis=1).sum(axis = 0, skipna = True).nlargest(5).index.to_list()
    df = df[df.columns.intersection(top_5)]
    df["Years"] = years
    
    fig = px.line(df, x="Years", y=top_5, markers=True)

    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = years,
            ticktext = years
        ),
        xaxis_title = "Years",
        yaxis_title = "Emails",
        legend_title = "Top 5 Companies",
        width = 900,
    )

    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def secure_plot():
    csv_results, years = sanitize('Secure')
    
    df = pandas.DataFrame.from_dict(csv_results)
    top_5 = df.drop(['Years'], axis=1).sum(axis = 0, skipna = True).nlargest(5).index.to_list()
    df = df[df.columns.intersection(top_5)]
    df["Years"] = years
    
    fig = px.line(df, x="Years", y=top_5, markers=True)

    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = years,
            ticktext = years
        ),
        xaxis_title = "Years",
        yaxis_title = "Emails",
        legend_title = "Top 5 Companies",
        width = 900,
    )

    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def total_plot():
    secure_results, secure_years = sanitize('Secure')
    unsecure_results, unsecure_years = sanitize('Unsecure')

    secure_df = pandas.DataFrame.from_dict(secure_results)
    secure_df = secure_df.drop(['Years'], axis=1)

    unsecure_df = pandas.DataFrame.from_dict(unsecure_results)
    unsecure_df = unsecure_df.drop(['Years'], axis=1)

    secure_rows = count_nonzero(secure_df, axis=1)
    unsecure_rows = count_nonzero(unsecure_df, axis=1)

    if len(secure_rows) == len(unsecure_rows):
        new_list = [0] * (len(secure_rows))

        for index, val in enumerate(secure_rows):
            if new_list[index] < secure_rows[index]:
                new_list[index] = secure_rows[index]

        for index, val in enumerate(unsecure_rows):
            if new_list[index] < unsecure_rows[index]:
                new_list[index] = unsecure_rows[index]

    if len(secure_years) > len(unsecure_years):
        years = secure_years
    else:
        years = unsecure_years

    fig = px.line(x=years, y=new_list, markers=True)

    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = years,
            ticktext = years
        ),
        xaxis_title = "Years",
        yaxis_title = "Emails",
        legend_title = "Trend of Email Tracking",
        width = 900,
    )

    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON
    
if __name__ == "__main__":
    # todo: init company table on start if not exists
    app.run()