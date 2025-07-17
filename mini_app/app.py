import dash
from dash import html, dcc, dash_table, callback, Input,  Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import os
import subprocess
import dash_bio
import numpy as np

from utils.pages.upload import upload_functions
from utils.pages.differential_expression import de_functions
from utils.helper_functions.main_functions import *

# By setting suppress_callback_exceptions=True, instruct Dash to ignore these mismatches during initialization, 
# allowing for more flexibility in how components and callbacks are dynamically created and linked. 
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.SANDSTONE]) 

# Define the logo with fixed width
logo = html.Img( 
    src='/assets/images/dna_2.png',  
    style={'height': '85%', 'width': '100%'}  # Set a fixed width for the logo
)

# Logo container
logo_container = html.Div(
    logo,
    style={'flex': '0 0 150px'},  # The logo will neither grow nor shrink
    className="d-flex align-items-center"
)

default_note_string = 'This app takes input in the form of gene-counts table output generated as a result of aligning sequencing reads to a reference, and various data analysis processes. Outputs a gene counts table and volcano plot to visualise the data.'

# To giver error alert
error_alert = dbc.Alert(
        id="upload-error-alert",
        is_open=False,
        dismissable=True,
        color="danger",
        style={'margin-top': '10px'}
    )

# Create an instance of the upload card
file_upload = upload_card('Upload the gene count file (Required)', 'upload-data')

# Navbar with logo and title
navbar = dbc.Navbar(
            dbc.Container(
                [
                    logo_container,
                    dbc.NavbarBrand("DESeq Analysis App", className="ms-2"),
                ],
                fluid=True,
                style={'display': 'flex'}
            ),
            color="dark",
            dark=True,
        )

# Divider lines
divider_line = html.Hr(className="mt-2 mb-4")

# Differential Expression Header
Diff_Exp_header = html.Div([
    html.H4(("Differential Expression"), style={'textAlign': 'center'}),
    divider_line,
])

# Differential expression selection dash table - selcting conditions
diff_exp_table = html.Div([
    dcc.Loading(
        id="loading-diff-exp-table",
        type="default",
        children=dash_table.DataTable( 
            id='table-dropdown',
            columns=[
                {'id': 'Samples', 'name': 'Samples'},
                {'id': 'Conditions', 'name': 'Conditions', 'presentation': 'dropdown'},
            ],
            css=[ {"selector": ".Select-menu-outer", "rule": "display: block !important;"},
                  {'selector': '.Select-menu-outer .Select-option', 'rule': 'color: black !important;'},
            ],
            editable=True,
            dropdown={
                'Conditions': {
                    'options': [
                        {'label': ' ', 'value': 'None'},
                        {'label': 'Control', 'value': 'Control'},
                        {'label': 'Treatment', 'value': 'Treatment'}
                    ]
                },
            },
            page_size=15,
        )
    )
])
# Button component for starting alignment
start_ana_btn = dbc.Button("Start Analysis", id='start-analysis-btn', color="dark", className="mt-3 btn-block")
# conditions table variable
conditions_table = dcc.Store(id='conditions_table')

# Showing the deseq results
deseq_results_table = html.Div([
    dash_table.DataTable(
        id='diff-exp-table',
        columns=[],  
        data=[],
        sort_action="native", 
        filter_action="native",
        page_size=20,
    )
])

# download button for the original results
download_deseq_results = dbc.Button("Download Original Results", id='results-download-btn', color="dark", className="mt-3 btn-block")

# Store results for download
download_deseq_results_component =  html.Div(
                [
                    dcc.Loading(
                        id='loading_deseq_download',
                        type='default',
                        children=[
                            dcc.Download(id='deseq_download_component')
                        ],
                    ),
                ],
                className='contain-spinner'
            )

volcano_plot_component = html.Div([
                'Effect Sizes',
                html.Br(),
                dcc.RangeSlider(
                    id = 'range-slider',
                    min = -10,
                    max = 10,
                    step= 0.05,
                    marks= {i: {'label': str(i)} for i in range(-10, 11)},
                    value= [-1, 1]
                ),
                html.Br(),
                html.Div(
                    dcc.Graph(
                        id='de_volcano_plot',
                        style={'height': '800px'}
                    )
                )
            ])


############################################################################################################################

# Define the app layout
app.layout = html.Div(
    className='container',
    children=[
        # Navigation bar
        navbar,
        html.Br(),
        # Main heading
        html.H4('Upload the count table and do the DESeq analysis', className='display-6', style={'textAlign': 'center', 'color': '#561fb6'}),
        # h 
        html.Div(default_note_string, style={'textAlign': 'center', 'font-size': 'small', 'white-space': 'pre-wrap'}),
        html.Br(),
        # Divider line
        divider_line,
        # Upload data area
        dbc.Row(
            [
                file_upload,
                error_alert,
                dbc.Col(
                    dbc.Row([
                        dbc.Col(
                            html.Div(id='filename-display', style={'textAlign': 'center'}),
                            width={"size": 12}
                        )
                    ]),
                ),
            ],
            style={'marginTop': '20px'}
        ),
        html.Br(),
        # Divider line
        divider_line,        
        # Storing uploaded data in dcc store to be accessed
        dcc.Store(id='gc-filestorage', storage_type='memory'),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([
                dbc.Label('Upload the count table in the "Upload files" tab and select the samples for differential expression analysis by selecting their experimental conditions.', 
                          className='mt-3', style={'font-size': 'small'}),
                html.Br(),
                diff_exp_table              
            ])),
            dbc.Col(html.Div([
                dbc.Label('Click "Start Analysis" to start the DE analysis once the required samples and conditions are selected.', 
                          className='mt-3', style={'font-size': 'small'}),
                dbc.Col(start_ana_btn, width={"size": 6, "offset": 4}),
                html.Br(),
                html.Div(id='loading-output')
            ]))
        ]),
        html.Br(),
        html.Br(),
        html.H5("Differential Expression Outputs", style={'textAlign': 'center'}),
        html.Hr(),
        html.Br(),
        # Storing the differential expression output
        dcc.Store(id='diff-exp-content', storage_type='memory'),
        html.Br(),
        dbc.Row([
            dbc.Col(deseq_results_table, md=12),
            html.Br(),
            dbc.Row([
                dbc.Col(download_deseq_results),
            ], style={'textAlign': 'center'}),
            # download_deseq_results,
            download_deseq_results_component,            
            dbc.Col(conditions_table)
        ]),
        html.Br(),
        html.Br(),
        html.H5("Volcano Plot", style={'textAlign': 'center'}),
        html.Hr(),  # Divider line
        dbc.Row([
            dcc.Loading(html.Div([
                'Effect Sizes',
                html.Br(),
                dcc.RangeSlider(
                    id='range-slider',
                    min=-10,
                    max=10,
                    step=0.05,
                    marks={i: {'label': str(i)} for i in range(-10, 11)},
                    value=[-1, 1]
                ),
                html.Br(),
                dcc.Graph(
                    id='de_volcano_plot',
                    style={'height': '800px'}
                )
            ]))
        ]),
    ],
    style={'margin': 0},
)


############################################################################################################################

# Calling the callback functions from /utils/pages
upload_functions()

de_functions()    

###################################################################################


###################################################################################


if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1', port=6688)