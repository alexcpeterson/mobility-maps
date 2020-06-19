from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import numpy as np
import re
import plotly.graph_objs as go
from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#Step 1: Launch the application
app = dash.Dash()

#Step 2: Import the dataset
covid = pd.read_csv(r'data/covid_confirmed.csv',dtype={'countyFIPS':str})

date_replace= {}
for date in covid.columns[4:]:
    if re.search(r'\d\/\d\d\/\d\d', date):
        date_replace[date] = datetime.strptime(date,'%m/%d/%y').strftime('%Y-%m-%d')
    else:
        date_replace[date] = datetime.strptime(date,'%m %d %y').strftime('%Y-%m-%d')
covid.rename(columns=date_replace,inplace=True)
dates= list(date_replace.values())

#Step 3: Create plotly figure
trace_1 = go.Scatter(x=covid[(covid.State == 'AL') & (covid['County Name'] == 'Autauga County')].columns[55:],
                    y=covid[(covid.State == 'AL') & (covid['County Name'] == 'Autauga County')][covid.columns[55:]].iloc[0].tolist(),
                    name = 'Alameda County, CA',
                    mode = 'markers'
                    )
layout = go.Layout(title = 'Cases Over Time')
fig = go.Figure(data=[trace_1],layout=layout)

#Step 4: Create Dash layout
states = [{'label' : i, 'value' : i} for i in covid.State.unique()]

app.layout = html.Div([
    #plot
    dcc.Graph(id='plot_id',figure = fig),
    html.Div([
    #dropdown
        html.P([
            html.Label('Choose a State'),
            dcc.Dropdown(id='state',
                        options = states,
                        value = 'AL')
        ], style = {'width' : '400px',
                    'fontSize' : '20px',
                    'padding-left' : '100px',
                    'display': 'inline-block'}),
        html.P([
            html.Label('Choose a County'),
            dcc.Dropdown(id = 'county',
                        value = 'Autauga County'
            )], style = {'width' : '400px',
                    'fontSize' : '20px',
                    'padding-left' : '100px',
                    'display': 'inline-block'})
        ])
])

#Step 5: Add callback functions
@app.callback(
    Output('county','options'),
    [Input('state','value')])
def update_county_dropdown(state):
    return [{'label': i, 'value': i} for i in covid[covid.State == state]['County Name']]
@app.callback(Output('plot_id','figure'),
                [Input('state','value'),
                Input('county','value')])
def update_figure(state,county):
    trace_2 = go.Scatter(
        x=covid[(covid.State == state) & (covid['County Name'] == county)].columns[55:],
        y= covid[(covid.State == state) & (covid['County Name'] == county)][covid.columns[55:]].iloc[0].tolist(),
        name = county + ', ' + state,
        mode = 'markers')
    fig = go.Figure(data=[trace_2],layout=layout)
    return fig

#Step 6: Add server clause
if __name__ == '__main__':
    app.run_server(debug=False)