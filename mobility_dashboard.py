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
us_state_abbrev = {
'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO',
'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'}
fips = pd.read_excel(r'data/fips_codes.xlsx',dtype={'fips':str})
covid = pd.read_csv(r'data/covid_confirmed.csv',dtype={'countyFIPS':str})
acs = pd.read_csv(r'data/2018_ACS.csv')
state_acs = pd.read_csv(r'data/ACS_2018_states.csv')
acs.drop(columns=['id'],inplace=True), state_acs.drop(columns=['id'], inplace=True)
state_acs.rename(columns = {'Geographic Area Name':'state'},inplace=True)
no_moe = acs.columns.str.contains('Margin')
cols = acs.columns.tolist()
acs = acs[[cols[x] for x in range(len(cols)) if not no_moe[x]]]
county_state = acs['Geographic Area Name'].tolist()
county, state = [],[]
for i in county_state:
    pattern = '(.*), (.*)'
    a = re.search(pattern, i)
    county.append(a.group(1)),state.append(a.group(2))
for c in range(len(county)):
    county[c] = county[c].replace(' County','')
    county[c] = county[c].replace('.','')
    county[c] = county[c].replace(' Parish','')
    county[c] = county[c].replace(' Borough','')
    county[c] = county[c].replace('city','City')
acs['county'] = county
acs['state']= state
acs.state = acs.state.map(us_state_abbrev).fillna(acs.state)
acs_fips = pd.merge(acs,fips[['fips','county','state']],how='left',left_on=['state','county'],right_on=['state','county'])
acs_fips['text'] = acs_fips.county +', ' +acs_fips.state
pop_col = 'Estimate!!RELATIONSHIP!!Population in households'
state_pop = state_acs[['state',pop_col]]
state_pop['state'] = state_pop.state.map(us_state_abbrev).fillna(state_pop.state)
state_pop.rename(columns={'Estimate!!RELATIONSHIP!!Population in households':'population'},inplace=True)
state_pop.state = state_pop.state.replace({'District of Columbia':'DC'})
county_pop = acs_fips[['fips','Estimate!!RELATIONSHIP!!Population in households']]
county_pop.rename(columns={'Estimate!!RELATIONSHIP!!Population in households':'population'},inplace=True)

no_moe = state_acs.columns.str.contains('Margin')
cols = state_acs.columns.tolist()
state_acs = state_acs[[cols[x] for x in range(len(cols)) if not no_moe[x]]]

date_replace= {}
for date in covid.columns[4:]:
    if re.search(r'\d\/\d\d\/\d\d', date):
        date_replace[date] = datetime.strptime(date,'%m/%d/%y').strftime('%Y-%m-%d')
    else:
        date_replace[date] = datetime.strptime(date,'%m %d %y').strftime('%Y-%m-%d')
covid.rename(columns=date_replace,inplace=True)
dates= list(date_replace.values())
covid_total = covid.copy()
#add state totals
for state in covid.State.unique():
    new_row = covid[covid.State == state].sum()
    new_row[0] = np.nan
    new_row[1] = 'State Total'
    new_row[2] = state
    new_row[3] = np.nan
    covid_total = covid_total.append(new_row,ignore_index=True)
#add united states total
new_row = covid.sum()
new_row[0] = np.nan
new_row[1] = 'Total'
new_row[2] = 'United States'
new_row[3] = np.nan
covid_total = covid_total.append(new_row,ignore_index=True)

#Step 3: Create plotly figure
trace_1 = go.Scatter(x=covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')].columns[55:],
                    y=(covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')]
                        [covid_total.columns[55:]].iloc[0].tolist()),
                    name = 'United States',
                    mode = 'markers'
                    )
layout = go.Layout(title = 'Coronavirus Cases Over Time',
                    title_font_size = 30,
                    title_x = .5,
                    height = 700, width = 1300
                    )
fig = go.Figure(data=[trace_1],layout=layout)

#Step 4: Create Dash layout
states = [{'label' : i, 'value' : i} for i in covid_total.State.unique()]

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Graph(id='plot_id',figure = fig)
            ],style={'padding-top':'25px','display':'flex','width':'70%'}
            ),
            html.Div([
                html.Div([
                    html.Label('Choose a State'),
                    dcc.Dropdown(id='state',
                            options = states,
                                value = 'United States')
                ], style = {'width' : '100%',
                            'fontSize' : '20px',
                            'padding-top': '200px',
                            'padding-left' : '0px',
                            'display': 'inline-block'}),
                html.Div([
                    html.Label('Choose a County'),
                    dcc.Dropdown(id = 'county',
                                value = 'State Total'
                    )], style = {'width' : '100%',
                            'fontSize' : '20px',
                            'padding-top' : '50px',
                            'display': 'inline-block'})
            ],style={'width':'25%'})
    ],style={'display':'flex'},className='wrapper'),
    
    html.Div([
        html.Div(
            id = 'stats',
            children = '',
        ),
    ],style = {'width' : '100%',
                    'fontSize' : '20px',
                    'padding-left' : '100px',
                    'display': 'inline-block'}
    )
])

#Step 5: Add callback functions
@app.callback(
    Output('county','options'),
    [Input('state','value')])
def update_county_dropdown(state):
    if state == 'United States':
        return [{'label': i, 'value': 'State Total'} for i in covid_total[covid_total.State == state]['County Name']]
    return [{'label': i, 'value': i} for i in covid_total[covid_total.State == state]['County Name']]
@app.callback(Output('plot_id','figure'),
                [Input('state','value'),
                Input('county','value')])
def update_figure(state,county='State Total'):
    if state == 'United States':
        trace_2 = go.Scatter(x=covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')].columns[55:],
                    y=(covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')]
                        [covid_total.columns[55:]].iloc[0].tolist()),
                    name = 'United States',
                    mode = 'markers'
                    )
        fig = go.Figure(data=[trace_2],layout=layout)
        return fig
    elif county not in covid_total[covid_total.State == state]['County Name'].tolist():
        trace_2 = go.Scatter(
        x=covid_total[(covid_total.State == state) & (covid_total['County Name'] == 'State Total')].columns[55:],
        y= covid_total[(covid_total.State == state) & (covid_total['County Name'] == 'State Total')][covid_total.columns[55:]].iloc[0].tolist(),
        name = county + ', ' + state,
        mode = 'markers')
        fig = go.Figure(data=[trace_2],layout=layout)
        return fig
    trace_2 = go.Scatter(
        x=covid_total[(covid_total.State == state) & (covid_total['County Name'] == county)].columns[55:],
        y= covid_total[(covid_total.State == state) & (covid_total['County Name'] == county)][covid_total.columns[55:]].iloc[0].tolist(),
        name = county + ', ' + state,
        mode = 'markers')
    fig = go.Figure(data=[trace_2],layout=layout)
    return fig
@app.callback(
    Output('stats','children'),
    [Input('state','value'),
    Input('county','value')])
def figure_stats(state,county='State Total'):
    if state == 'United States':
        return ''
    elif county not in covid_total[covid_total.State == state]['County Name'].tolist():
        usa_pop = state_pop.population.sum()
        proportion_pop = state_pop[state_pop.state == state].population.sum() / usa_pop * 100
        total_cases = covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')][covid_total.columns[-1]].sum()
        state_cases = covid_total[(covid_total.State == state) & (covid_total['County Name'] == 'State Total')][covid.columns[-1]].sum()
        proportion_cases = state_cases / total_cases * 100
        full_state = [key for key,val in us_state_abbrev.items() if val == state][0]
        text = "{} accounts for {:2f}% of the population in the United States and for {:2f}% of the total COVID-19 cases in the United States"
        return text.format(full_state,proportion_pop,proportion_cases)
    if 'Total' in county:
        usa_pop = state_pop.population.sum()
        proportion_pop = state_pop[state_pop.state == state].population.sum() / usa_pop * 100
        total_cases = covid_total[(covid_total.State == 'United States') & (covid_total['County Name'] == 'Total')][covid_total.columns[-1]].sum()
        state_cases = covid_total[(covid_total.State == state) & (covid_total['County Name'] == county)][covid.columns[-1]].sum()
        proportion_cases = state_cases / total_cases * 100
        full_state = [key for key,val in us_state_abbrev.items() if val == state][0]
        text = "{} accounts for {:2f}% of the population in the United States and for {:2f}% of the total COVID-19 cases in the United States"
        return text.format(full_state,proportion_pop,proportion_cases)
    else:
        cty_pop = (county_pop[county_pop.fips == covid[(covid.State == state) & (covid['County Name'] == county)]
            .countyFIPS.sum()].population.sum())
        ste_pop = state_pop[state_pop.state == state].population.sum()
        proportion_pop = cty_pop / ste_pop * 100 
        state_cases = covid_total[(covid_total.State == state) & (covid_total['County Name'] == 'State Total')][covid_total.columns[-1]].sum()
        county_cases = covid_total[(covid_total.State == state) & (covid_total['County Name'] == county)][covid_total.columns[-1]].sum()
        proportion_cases = county_cases / state_cases * 100 
        text =text = "{}, {} accounts for {:.2f}% of the state's population and for {:.2f}% of the state's total COVID-19 cases."
        return text.format(county,state,proportion_pop,proportion_cases)
#Step 6: Add server clause
if __name__ == '__main__':
    app.run_server(debug=False)