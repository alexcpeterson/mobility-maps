from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import numpy as np
import re
import plotly.graph_objs as go
from datetime import datetime
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
usa_regions = {
    'WA' : 'North West','OR' : 'North West','ID' : 'North West','MT' : 'North West','WY' : 'North West',
    'CA' : 'West','NV' : 'West','AK' : 'West','HI' : 'West',
    'UT' : 'South West','NM' : 'South West','CO' : 'South West','AZ' : 'South West','TX' : 'South West','OK' : 'South West',
    'ND' : 'Mid-West','SD' : 'Mid-West','NE' : 'Mid-West','KS' : 'Mid-West','WI' : 'Mid-West','IA' : 'Mid-West','MO' : 'Mid-West',
    'MI' : 'Mid-West','IL' : 'Mid-West','IN' : 'Mid-West','KY' : 'Mid-West','OH' : 'Mid-West','MN' : 'Mid-West',
    'AR' : 'South East','LA' : 'South East','AL' : 'South East','MS' : 'South East','TN':'South East','GA':'South East','FL':'South East',
    'SC' : 'South East','NC' : 'South East',
    'VA' : 'Mid-Atlantic','WV' : 'Mid-Atlantic','PA' : 'Mid-Atlantic','MD' : 'Mid-Atlantic','DE' : 'Mid-Atlantic','NJ' : 'Mid-Atlantic',
    'NY' : 'Mid-Atlantic','DC' : 'Mid-Atlantic',
    'CT' : 'North East','RI' : 'North East','VT' : 'North East','NH' : 'North East','MA' : 'North East','ME' : 'North East'  
}
fips = pd.read_excel(r'data/fips_codes.xlsx',dtype={'fips':str})
covid = pd.read_csv(r'data/covid_confirmed.csv',dtype={'countyFIPS':str})
acs = pd.read_csv(r'data/2018_ACS.csv')
state_acs = pd.read_csv(r'data/ACS_2018_states.csv')
acs.drop(columns=['id'],inplace=True), state_acs.drop(columns=['id'], inplace=True)
state_acs.rename(columns = {'Geographic Area Name':'state'},inplace=True)
no_moe = acs.columns.str.contains('Margin')
cols = acs.columns.values
acs = acs[[cols[x] for x in range(len(cols)) if not no_moe[x]]]
county_state = acs['Geographic Area Name'].values
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
cols = state_acs.columns.values
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

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
full_df = pd.read_csv(r'mobility_report_US.csv',dtype={'fips':str})
full_df_copy = full_df.copy()
new_dates = []
for date in full_df_copy.date:
    new_dates.append(datetime.strptime(date,'%d %m %y').strftime('%Y-%m-%d'))
full_df_copy['date'] = new_dates
full_df_copy.state = full_df_copy.state.map(us_state_abbrev).fillna(full_df_copy.state)
full_final = full_df_copy
final_by_state = full_final[(full_final.state != 'Total') & (full_final.county == 'Total')]
final_by_state.state = final_by_state.replace({'District of Columbia':'DC'})
full_final = full_final[(full_final.state != 'Total') & (full_final.county != 'Total')]
full_final['text'] = full_final.county + ', ' + full_final.state
test_state = final_by_state.copy()
cases_by_state = pd.DataFrame(columns=['cases','state'])
for state in covid.State.unique():
    state_cases = covid[covid.State == state][covid.columns[4:]].sum().to_frame().rename(columns={0:'cases'})
    state_cases['state'] = [state for _ in range(len(state_cases))]
    cases_by_state = cases_by_state.append(state_cases)
cases_by_state['date'] = cases_by_state.index
mob_case_state = pd.merge(test_state,cases_by_state,left_on=['date','state'],right_on=['date','state'])
mob_case_state['region'] = mob_case_state.state.map(usa_regions)
cases_by_state['region'] = cases_by_state.state.map(usa_regions)
proportion = pd.DataFrame(columns=['cases'])
for state in mob_case_state.state.unique():
    prop = (mob_case_state[mob_case_state.state == state].cases / state_pop[state_pop.state == state].population.sum()).to_frame()
    proportion = proportion.append(prop)
mob_case_state['proportion'] = proportion.cases*100

scatter_labels = {
    'grocery and pharmacy' : 'Grocery Stores and Pharmacies',
    'retail' : 'Retail Locations',
    'parks' : 'Parks',
    'workplaces' : 'Workplaces',
    'residential' : 'Residential Areas',
    'transit stations' : 'Transit Stations'
}