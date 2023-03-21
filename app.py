from flask import Flask, render_template, request, send_file, Response

import hashlib

import pandas
from imapencoding import login_mail_client, get_mail, get_user, add_user

from numpy import count_nonzero
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.debug = True

# todo: write companies that dont exist in disconnect me repo to own 'uncertain' file and take off further scans


@app.route("/home")
@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        email_address = request.form.get('email')
        password = request.form.get('password')

        # hash email
        email_md5 = hashlib.md5(email_address.encode())
        email_md5 = email_md5.hexdigest()

        # is hash in users table?
        user = get_user(email_md5)
        if user != "":
            # user exists, perform incremental scan
            mail = login_mail_client(email_address, password)
            email_scanned, links_found = get_mail(mail, email_md5)
        else:
            # user does not exist, scan email
            mail = login_mail_client(email_address, password)
            email_scanned, links_found = get_mail(mail, email_md5)

            user_data = (email_md5, email_scanned, links_found, None)
            add_user(user_data, email_md5)

        unsecureJSON = unsecure_plot(email_md5)
        secureJSON = secure_plot(email_md5)
        totalJSON = total_plot(email_md5)

        tableJSON = generate_table(email_md5)

        company, company_year = additional_data(email_md5)

        resp = Response(render_template("results.html", email_scanned=email_scanned, links_found=links_found, unsecureJSON=unsecureJSON, secureJSON=secureJSON, totalJSON=totalJSON, company=company, company_year=company_year, tableJSON=tableJSON))
        
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

def sanitize(security_level, email_md5):
    results = defaultdict(list)

    csv = pandas.read_csv(r'{}_results_data.csv'.format(email_md5))

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
            if type(years[count]) == str:
                company_df = csv[(csv['Tracking Service'] == company) & (csv['Date'] == years[count])]
            elif type(years[count]) == int:
                company_df = csv[(csv['Tracking Service'] == company) & (csv['Year'] == years[count])]

            freq = count_nonzero(company_df[security_level])
            results[company].append(freq)
            count += 1
    
    return results, years

def unsecure_plot(email_md5):
    csv_results, years = sanitize('Unsecure', email_md5)
    
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

def secure_plot(email_md5):
    csv_results, years = sanitize('Secure', email_md5)
    
    df = pandas.DataFrame.from_dict(csv_results)
    top_5 = df.drop(['Years'], axis=1).sum(axis = 0, skipna = True).nlargest(5).index.to_list()
    df = df[df.columns.intersection(top_5)]
    df["Years"] = years

    top_1 = df.drop(['Years'], axis=1).sum(axis = 0, skipna = True).nlargest(1).index.to_list()
    print(top_1[0])
    
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

def total_plot(email_md5):
    secure_results, secure_years = sanitize('Secure', email_md5)
    unsecure_results, unsecure_years = sanitize('Unsecure', email_md5)

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

def additional_data(email_md5):
    csv_results, years = sanitize('Secure', email_md5)
    
    df = pandas.DataFrame.from_dict(csv_results)
    top_1_company = df.drop(['Years'], axis=1).sum(axis = 0, skipna = True).nlargest(1).index.to_list()
    emails_sent = df[top_1_company[0]].max()
    test = df[top_1_company[0]] == emails_sent
    test = df.loc[test]
    top_year = test['Years'].to_list()

    return top_1_company[0], top_year[0]


def generate_table(email_md5):
    results = defaultdict(list)

    csv = pandas.read_csv(r'{}_results_data.csv'.format(email_md5))

    companies = csv['Domain'].unique()
    results['Rank'] = [x for x in range(len(companies))]
    
    for company in companies:
        freq = csv['Domain'].value_counts()[company]
        tracking_services = csv.query(f'Domain == "{company}"')['Tracking Service'].unique()

        results["Company"].extend([company])
        results["Emails Sent"].extend([freq])
        results["Most Common Ad Tracking Services Found"].extend([list(tracking_services)])

    df = pandas.DataFrame.from_dict(results)
    df = df.sort_values('Emails Sent',ascending=False).head(10)
    df['Rank'] = [x for x in range(1, 11)]

        # values=list(df.columns),
    fig = go.Figure(data=[go.Table(
    columnorder = [1, 2, 3, 4],
    columnwidth = [20, 30, 20, 30],
    header=dict(values=["<b>Rank</b>", "<b>Company</b>", "<b>Emails Sent</b>", "<b>Tracking Services Used</b>"],
                line_color='white', fill_color='white',
                align='left', font=dict(color='black', size=16)),
    cells=dict(values=[df.Rank, df.Company, df["Emails Sent"], df["Most Common Ad Tracking Services Found"]],
               align='left', fill_color='white', font=dict(color='black', size=14)))
])
    
    fig.update_layout(width=900, height=410,  paper_bgcolor='white', plot_bgcolor='black')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON
    

    
if __name__ == "__main__":
    app.run()