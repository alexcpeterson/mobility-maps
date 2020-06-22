from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import numpy as np
import re
import plotly.graph_objs as go
from datetime import datetime
import math
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import data_cleaning as dc

#Launch the application
app = dash.Dash(suppress_callback_exceptions=True)

#Create plotly figures
## Covid Cases Over Time Scatter Plot
case_trace_1 = (go.Scatter(
    x=dc.covid_total[(dc.covid_total.State == 'United States') 
    & (dc.covid_total['County Name'] == 'Total')].columns[55:],
    y=dc.covid_total[(dc.covid_total.State == 'United States') & 
    (dc.covid_total['County Name'] == 'Total')]
    [dc.covid_total.columns[55:]].iloc[0].values,
    name = 'United States',
    mode = 'markers')
    )
case_layout = go.Layout(title = 'Coronavirus Cases Over Time',
    title_font_size = 30,
    title_x = .5,
    height = 700, width = 1200
    )
case_fig = go.Figure(data=[case_trace_1],layout=case_layout)

##Mobility Scatter Plot
mob_scatter_fig = (px.scatter(dc.mob_case_state[dc.mob_case_state.date.isin(dc.dates[55:])],
    x='grocery and pharmacy', y='cases',animation_frame = 'date',animation_group = 'state',
    color = 'region', hover_name = 'state',
    size=dc.mob_case_state[dc.mob_case_state.date.isin(dc.dates[55:])].proportion.tolist(),
    log_y = True, range_x = [-70,40],range_y = [1,500000])
    )
mob_scatter_fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1500
mob_scatter_fig.update_layout(
    title_text = 'Comparison of Mobility to Grocery Stores and Pharmacies and COVID-19 Cases by Geographic Region',
    title_x = .5,
    height = 700
    )

#Create Dash layout
states = [{'label' : i, 'value' : i} for i in dc.covid_total.State.unique()]

#tab-1
covid_cases_html = html.Div([
     html.Div([
        html.Div([
            dcc.Graph(id='cases_fig',figure = case_fig)
            ],style={'padding-top':'25px','display':'flex','width':'80%'}),
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
                    value = 'State Total')
            ], style = {'width' : '100%',
                        'fontSize' : '20px',
                        'padding-top' : '50px',
                        'display': 'inline-block'})
        ],style={'width':'19%'})
    ],style={'display':'flex'},className='wrapper'),
    html.Div([
        html.Div(
            id = 'stats',
            children = ''),
    ],style = {'width' : '100%',
                'fontSize' : '20px',
                'padding-left' : '100px',
                'display': 'inline-block'}
    )
])
#tab-2

#tab-3
mobility_scatter_html = html.Div([
    dcc.RadioItems(
        id = 'mobility_scatter_picker',
        options = [
            {'label' : 'Grocery and Pharmacy','value' : 'grocery and pharmacy'},
            {'label' : 'Retail','value' : 'retail'},
            {'label' : 'Parks', 'value' : 'parks'},
            {'label' : 'Workplaces', 'value' : 'workplaces'},
            {'label' : 'Residential', 'value' : 'residential'},
            {'label' : 'Transit Stations', 'value' : 'transit stations'}
        ],
        value = 'grocery and pharmacy',
        labelStyle = {'display' : 'inline-block','fontSize' : 20,'padding-top': '25px','padding-left' : '100px'}
    ),
    html.Div([
        dcc.Graph(id='mob_scatter',figure = mob_scatter_fig)
    ],style = {'padding-top' : '25px'})
])

app.layout = html.Div([
    dcc.Tabs(id='tabs', value = 'tab-3', children =[
        dcc.Tab(label = 'COVID-19 Cases',value = 'tab-1'),
        #dcc.Tab(label = 'Mobility Maps',value = 'tab-2'),
        dcc.Tab(label = 'Mobility Comparisons',value = 'tab-3')
    ]),
    html.Div(id = 'tab-content')
])

#Step 5: Add callback functions
#render different tabs
@app.callback(
    Output('tab-content','children'),
    [Input('tabs','value')])
def render_content(tab):
    if tab is not None:
        if tab == 'tab-1':
            return covid_cases_html
        elif tab == 'tab-2':
            return None #removed tab
        elif tab == 'tab-3':
            return mobility_scatter_html
#update second dropdown
@app.callback(
    Output('county','options'),
    [Input('state','value')])
def update_county_dropdown(state):
    if state == 'United States':
        return ([{'label': i, 'value': 'State Total'} for i in 
        dc.covid_total[dc.covid_total.State == state]['County Name']])
    return ([{'label': i, 'value': i} for i in 
        dc.covid_total[dc.covid_total.State == state]['County Name']])
#update cases figure
@app.callback(
    Output('cases_fig','figure'),
    [Input('state','value'),
    Input('county','value')])
def update_case_figure(state,county='State Total'):
    # handle default action on United States.
    if state == 'United States':
        case_trace_2 = (go.Scatter(
        x=dc.covid_total[(dc.covid_total.State == 'United States') & 
        (dc.covid_total['County Name'] == 'Total')].columns[55:],
        y=dc.covid_total[(dc.covid_total.State == 'United States') & 
        (dc.covid_total['County Name'] == 'Total')][dc.covid_total.columns[55:]].iloc[0].values,
        name = 'United States',
        mode = 'markers')
        )
        case_fig = go.Figure(data=[case_trace_2],layout=case_layout)
        return case_fig
    # handle cases swapping between states after selecting a county, defaults to state total graph.
    elif county not in dc.covid_total[dc.covid_total.State == state]['County Name'].values:
        case_trace_2 = (go.Scatter(
        x=dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == 'State Total')].columns[55:],
        y= dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == 'State Total')][dc.covid_total.columns[55:]].iloc[0].values,
        name = county + ', ' + state,
        mode = 'markers')
        )
        case_fig = go.Figure(data=[case_trace_2],layout=case_layout)
        return case_fig
    #when state, county pair has been sucessfully passed
    else:
        case_trace_2 = (go.Scatter(
        x=dc.covid_total[(dc.covid_total.State == state) & (
        dc.covid_total['County Name'] == county)].columns[55:],
        y= dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == county)][dc.covid_total.columns[55:]].iloc[0].values,
        name = county + ', ' + state,
        mode = 'markers')
        )
    case_fig = go.Figure(data=[case_trace_2],layout=case_layout)
    return case_fig
#update cases stats
@app.callback(
    Output('stats','children'),
    [Input('state','value'),
    Input('county','value')])
def figure_stats(state,county='State Total'):
    #page landing action
    if state == 'United States':
        return ''
    # when swapping between states when a county has been selects, shows stats for state total
    elif county not in dc.covid_total[dc.covid_total.State == state]['County Name'].values:
        usa_pop = dc.state_pop.population.sum()
        proportion_pop = dc.state_pop[dc.state_pop.state == state].population.sum() / usa_pop * 100
        total_cases = (dc.covid_total[(dc.covid_total.State == 'United States') & 
        (dc.covid_total['County Name'] == 'Total')][dc.covid_total.columns[-1]].sum())
        state_cases = (dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == 'State Total')][dc.covid_total.columns[-1]].sum())
        proportion_cases = state_cases / total_cases * 100
        full_state = [key for key,val in dc.us_state_abbrev.items() if val == state][0]
        text = "{} accounts for {:2f}% of the population in the United States and \
            for {:2f}% of the total COVID-19 cases in the United States"
        return text.format(full_state,proportion_pop,proportion_cases)
    #when displaying state total cases
    if 'Total' in county:
        usa_pop = dc.state_pop.population.sum()
        proportion_pop = dc.state_pop[dc.state_pop.state == state].population.sum() / usa_pop * 100
        total_cases = (dc.covid_total[(dc.covid_total.State == 'United States') & 
        (dc.covid_total['County Name'] == 'Total')][dc.covid_total.columns[-1]].sum())
        state_cases = (dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == county)][dc.covid_total.columns[-1]].sum())
        proportion_cases = state_cases / total_cases * 100
        full_state = [key for key,val in dc.us_state_abbrev.items() if val == state][0]
        text = "{} accounts for {:2f}% of the population in the United States and \
            for {:2f}% of the total COVID-19 cases in the United States"
        return text.format(full_state,proportion_pop,proportion_cases)
    #when state,county properly passed
    else:
        cty_pop = (dc.county_pop[dc.county_pop.fips == dc.covid[(dc.covid.State == state) & 
        (dc.covid['County Name'] == county)].countyFIPS.sum()].population.sum())
        ste_pop = dc.state_pop[dc.state_pop.state == state].population.sum()
        proportion_pop = cty_pop / ste_pop * 100 
        state_cases = (dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == 'State Total')][dc.covid_total.columns[-1]].sum())
        county_cases = (dc.covid_total[(dc.covid_total.State == state) & 
        (dc.covid_total['County Name'] == county)][dc.covid_total.columns[-1]].sum())
        proportion_cases = county_cases / state_cases * 100 
        text =text = "{}, {} accounts for {:.2f}% of the state's population and \
            for {:.2f}% of the state's total COVID-19 cases."
        return text.format(county,state,proportion_pop,proportion_cases)
#update scatter
@app.callback(
    Output('mob_scatter','figure'),
    [Input('mobility_scatter_picker','value')])
def update_mob_scatter_figure(metric):
    def scatter_range(metric):
        if metric == 'parks':
            return [-100,250]
        lower = dc.mob_case_state[dc.mob_case_state.date.isin(dc.dates[55:])][metric].min()
        upper = dc.mob_case_state[dc.mob_case_state.date.isin(dc.dates[55:])][metric].max()
        return [int(math.floor(lower/10.0))*10,int(math.ceil(upper / 10.0)) * 10]
    mob_scatter_fig = (px.scatter(dc.mob_case_state[dc.mob_case_state.date.isin(dc.dates[55:])],
        x=metric, y='cases',animation_frame = 'date',animation_group = 'state',
        color = 'region', hover_name = 'state',size=dc.mob_case_state
        [dc.mob_case_state.date.isin(dc.dates[55:])].proportion.tolist(),
        log_y = True, range_x = scatter_range(metric),range_y = [1,500000])
    )
    mob_scatter_fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1500
    mob_scatter_fig.update_layout(
        title_text = 'Comparison of Mobility to ' + dc.scatter_labels[metric] + \
            ' and COVID-19 Cases by Geographic Region',
        title_x = .5,
        height = 700
    )
    return mob_scatter_fig
#Step 6: Add server clause
if __name__ == '__main__':
    app.run_server(debug=False)