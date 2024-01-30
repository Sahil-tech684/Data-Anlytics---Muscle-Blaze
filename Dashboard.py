import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

import pandas as pd
data = pd.read_json('./data/cleaned_data.json')

external_stylesheets = ['https://fonts.googleapis.com/css?family=Lato&display=swap']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

flavor_options = [{'label': flavor, 'value': flavor} for flavor in ['All'] + data['flavour'].unique().tolist()]
supplement_options = [{'label': supplement, 'value': supplement} for supplement in ['All'] + data['supplimentName'].unique().tolist()]
weight_options = [{'label': weight, 'value': weight} for weight in ['All'] + [0.04, 0.4 , 0.5 , 0.6 , 0.75, 0.85, 1.  , 1.75, 1.82, 2.  , 4.  ]]

app.layout = html.Div(children=[
    # Header
    html.H1("Product Analysis Dashboard", style={'textAlign': 'center', 'color': 'black'}),

    # Filter Dropdowns
    html.Div([
        # Flavor Dropdown
        html.Div([
            html.Label('Select a Flavor:', style={'color': 'black', 'fontFamily': 'Lato'}),
            dcc.Dropdown(
                id='flavor-dropdown',
                options=flavor_options,
                value='All',
                multi=False,
                clearable=False,
                style={'width': '80%', 'fontFamily': 'Lato'}
            ),
        ], style={'width': '50%'}),

        # Supplement Dropdown
        html.Div([
            html.Label('Select a Supplement:', style={'color': 'black', 'fontFamily': 'Lato'}),
            dcc.Dropdown(
                id='supplement-dropdown',
                options=supplement_options,
                value='All',
                multi=False,
                clearable=False,
                style={'width': '80%', 'fontFamily': 'Lato'}
            ),
        ], style={'width': '50%', 'fontFamily': 'Lato'}),
    ], style={'display': 'flex'}),

    # First Scatter Plot
    dcc.Graph(id='product-analysis-plot'),

    # Weight Dropdown
    html.Div([
        html.Label('Select a Weight (in Kg):', style={'color': 'black', 'fontFamily': 'Lato'}),
        dcc.Dropdown(
            id='weight-dropdown',
            options=weight_options,
            value='All',
            multi=False,
            clearable=False,
            style={'width': '50%', 'fontFamily': 'Lato'}
        ),
    ], style={'margin-top': '20px'}),

    # Second Bar Plot
    dcc.Graph(id='product-analysis-plot2'),

], style={'backgroundColor': 'white', 'padding': '20px', 'fontFamily': 'Lato'})



@app.callback(
    Output('product-analysis-plot', 'figure'),
    [Input('flavor-dropdown', 'value'), Input('supplement-dropdown', 'value')]
)
def update_plot(selected_flavor, selected_supplement):
    if selected_supplement != 'All':
        filtered_data = data[data.supplimentName == selected_supplement]
    else:
        filtered_data = data

    if selected_flavor == 'All':
        filtered_data = filtered_data.groupby(['weight'])[['name', 'totalRating', 'rating']].agg({
            'name': 'count',
            'totalRating': 'sum',
            'rating': 'mean'
        }).rename(columns={'name': 'No. Of Products', 'rating': 'Average Rating'}).sort_values('Average Rating', ascending=False).reset_index()
    else:
        filtered_data = filtered_data[filtered_data['flavour'] == selected_flavor].groupby(['weight'])[['name', 'totalRating', 'rating']].agg({
            'name': 'count',
            'totalRating': 'sum',
            'rating': 'mean'
        }).rename(columns={'name': 'No. Of Products', 'rating': 'Average Rating'}).sort_values('Average Rating', ascending=False).reset_index()

    fig = px.scatter(
        data_frame=filtered_data,
        x='weight', y='Average Rating', size='totalRating',
        hover_data=['weight', 'No. Of Products', 'totalRating', 'Average Rating'],
        labels={'weight': 'Product Weight', 'Average Rating': 'Average Rating'},
        title=f'Product Analysis by Weight for {selected_flavor + " flavours" if selected_flavor == "All" else selected_flavor + " flavour"} and {selected_supplement + " Supplements" if selected_supplement == "All" else selected_supplement}',
        color='No. Of Products',
        color_continuous_scale=px.colors.sequential.Viridis,
        size_max=60,
    )

    fig.update_layout(
        xaxis_title='Product Weight',
        yaxis_title='Average Rating',
        font=dict(family='Arial', size=12, color='black'),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hoverlabel=dict(bgcolor='white', font_size=14, font_family='Arial'),
        xaxis=dict(gridcolor='black', layer='below traces'),
        yaxis=dict(gridcolor='black', layer='below traces'),
    )

    fig.update_traces(
        hovertemplate='Weight: %{x:.2f} kg<br>' +
                      'Average Rating: %{y:.2f}<br>' +
                      'No. Of Products: %{customdata[0]:,}<br>' +
                      'No. Of Ratings: %{customdata[1]}<br>'
    )

    return fig



@app.callback(
    Output('product-analysis-plot2', 'figure'),
    [Input('flavor-dropdown', 'value'), Input('weight-dropdown', 'value')]
)
def update_plot(selected_flavor, selected_weight):
    selected_weight = 0.6000000000000001 if selected_weight == 0.6 else selected_weight

    if selected_weight != 'All':
        filtered_data = data[data.weight == selected_weight]
    else:
        filtered_data = data

    if selected_flavor == 'All':
        filtered_data = filtered_data[filtered_data.totalRating > 0].groupby('supplimentName')[['rating', 'totalRating']].agg({'rating': 'mean', 'totalRating': sum}).reset_index().rename(columns= {'totalRating': 'No. Of Products'})
    else:
        filtered_data = filtered_data[filtered_data.flavour == selected_flavor].groupby('supplimentName')[['rating', 'totalRating']].agg({'rating': 'mean', 'totalRating': sum}).reset_index().rename(columns= {'totalRating': 'No. Of Products'})

    fig = px.bar(
        data_frame=filtered_data,
        x='supplimentName', y='rating', hover_data=['No. Of Products'],
        labels={'supplimentName': 'Supplement Name', 'rating': 'Average Rating'},
        title=f'Average Ratings for {selected_flavor} Supplements',
        color='No. Of Products',
        color_continuous_scale=px.colors.sequential.Viridis,
    )

    fig.update_layout(
        xaxis_title='Supplement Name',
        yaxis_title='Average Rating',
        font=dict(family='Arial', size=12, color='black'),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hoverlabel=dict(bgcolor='white', font_size=14, font_family='Arial'),
        xaxis=dict(gridcolor='black', layer='below traces'),
        yaxis=dict(gridcolor='black', layer='below traces'),
    )

    fig.update_traces(
        hovertemplate='Supplement Name: %{x} <br>' +
                      'Average Rating: %{y:.2f}<br>' +
                      'No. Of Products: %{customdata[0]:,}'
    )

    fig.update_yaxes(range=[filtered_data['rating'].min() - 0.1, filtered_data['rating'].max() + 0.1])
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)