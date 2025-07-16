from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
from io import StringIO

# Function to create the default upload card component
def upload_card(header_text, upload_id):
    return dbc.Col(
        [
            dbc.Card(
                [
                    dbc.CardHeader(html.H6(header_text, style={'textAlign': 'center', 'color': 'white'})),
                    dcc.Upload(
                        id=upload_id,
                        children=html.Div('Drag and Drop or Select Files', style={'backgroundColor': 'white'}),
                        style={
                            'width': '100%',  
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed lightgray',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': 'auto' 
                        },
                        multiple=True
                    ),
                ],
                id = f'{upload_id}_header',
                style={'boxShadow': '0px 4px 8px rgba(0,0,0,0.2)', 'backgroundColor': 'black'}
            ),
        ]
    )

# Function to parse contents of the uploaded file
def parse_contents(contents):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in content_type:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in content_type:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, 'Unsupported file type'
    except Exception as e:
        return None, str(e)

    return df, None