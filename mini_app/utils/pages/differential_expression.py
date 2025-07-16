from dash import html, callback, Input,  Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import os
import subprocess
import dash_bio
import numpy as np
import io
from io import StringIO


def de_functions():
    # Callback to update the sample names in the table for dropdowns
    @callback(
        Output('table-dropdown', 'data'),
        [Input('gc-filestorage', 'data')]
    )
    def update_sample_names(input_data):
        if input_data:
            df = pd.read_json(StringIO(input_data), orient='split')
            sample_names = df.columns[1:]
            conditions = [' ' for sample in sample_names] # Shows empty at first
            df_samples = pd.DataFrame({'Samples': sample_names, 'Conditions': conditions})
            return df_samples.to_dict('records')
        else:
            print('Sorry no data')
            return []
        

    # Define the output for the new callback to update the conditions table 
    @callback(
        Output('conditions_table', 'data'),
        [Input('table-dropdown', 'data')]
    )
    def update_conditions_table(table_data):
        if table_data:
            df = pd.DataFrame(table_data, index=None)

            df_filtered = df[df['Conditions'].isin(['Control', 'Treatment'])]

            print(df_filtered)
            
            return df_filtered.to_dict('records')
        else:
            return []
        

###################################################################################################################

    # Running the DE analysis
    @callback(
    Output('diff-exp-content', 'data'),
    [Input('start-analysis-btn', 'n_clicks')],
    [State('conditions_table', 'data'),
    State('gc-filestorage', 'data')],
    prevent_initial_call=True
    )
    def start_deseq(n_clicks, conditions, input_data):
        if n_clicks:
            # Loading the conditions table and filtering only the samples selected
            conditions_table = pd.DataFrame(conditions, index=None)
            samples_required = conditions_table['Samples'].tolist()
            
            # Loading the data and keeping only the selected samples
            de_data = pd.read_json(StringIO(input_data), orient='split')

            gene_id_column = de_data.columns[0]

            required_columns = [gene_id_column] + samples_required

            de_data_filtered = de_data[required_columns]

            # Making directory for DESEQ analysis
            os.makedirs('utils/outputs/DESEQ', exist_ok=True)

            # Making conditions and deseq data files
            conditions_table.to_csv('utils/outputs/DESEQ/conditions_table.tsv', sep= '\t', index=False)
            de_data_filtered.to_csv('utils/outputs/DESEQ/df_de.csv', index=False)

            # DE ouput
            de_out = 'utils/outputs/DESEQ/de_out.csv'

            # R-script
            script_path = 'utils/helper_functions/DGE_deseq2.r'

            # R-Script for running DESEQ
            print(f'Rscript {script_path} utils/outputs/DESEQ/df_de.csv utils/outputs/DESEQ/conditions_table.tsv de_out')

            #Running DESEQ
            res = subprocess.check_output(f'Rscript {script_path} utils/outputs/DESEQ/df_de.csv utils/outputs/DESEQ/conditions_table.tsv Control Treatment {de_out}', shell=True)

            # Load in the DE framework, present it on page, give it to store
            de_df = pd.read_csv(de_out)

            de_df = de_df.rename(columns={'Unnamed: 0': 'GeneID'})

            # Store de df in json store
            de_store = de_df.to_json(date_format='iso', orient='split', double_precision=15)
        

        return de_store

    # Callback to update the differential expression table - original data
    @callback(
        [Output('diff-exp-table', 'data', allow_duplicate=True),
        Output('diff-exp-table', 'columns', allow_duplicate=True)],
        Input('diff-exp-content', 'data'),
        prevent_initial_call=True
    )
    def update_diff_exp_table(input_data):
        if input_data:
            # Parse the input data and extract columns and data
            df = pd.read_json(StringIO(input_data), orient='split', precise_float=True)

            # Replace NaN and inf values with underscores
            df.replace([np.nan, np.inf, -np.inf], '_', inplace=True)
            
            # Fill remaining NaN values with underscores
            df.fillna('_', inplace=True)
            
            columns = [{'name': col, 'id': col} for col in df.columns]
            data = df.to_dict('records')
            return data, columns
        else:
            return [], []

    # Downloading the deseq results - Unaltered data
    @callback(
        Output('deseq_download_component', 'data', allow_duplicate=True),
        Input('results-download-btn', 'n_clicks'),
        Input('diff-exp-content', 'data'),
        prevent_initial_call=True
    )    
    def download_original_deseq_results(n_clicks, input_data):
        if input_data:
            # Parse the input data and extract columns and data
            df = pd.read_json(StringIO(input_data), orient='split', precise_float=True)
            columns = [{'name': col, 'id': col} for col in df.columns]
            data = df.to_dict('records')

            if n_clicks:
                if data is None or columns is None:
                    # If data or columns are not available, prevent download
                    raise PreventUpdate
                else:
                    # Prepare CSV content
                    csv_string = ','.join([col['name'] for col in columns]) + '\n'
                    for row in data:
                        csv_string += ','.join([str(row[col['id']]) for col in columns]) + '\n'

                    # Create download dictionary
                    return dict(content=csv_string, filename='Deseq_results.csv')
                
    # Creating the Volcano plot from deseq data
    @callback(
    Output('de_volcano_plot', 'figure'),
    Input('range-slider', 'value'),
    Input('diff-exp-content', 'data'),
    prevent_initial_call=True
    )
    def make_volcano_plot(effects, input_data):
        if input_data:
            # Parse the input data and extract columns and data
            df = pd.read_json(StringIO(input_data), orient='split', precise_float=True)

            df = df.dropna(subset=['padj'])  # Remove rows with NaN padj-values # 'pvalue'
            df = df.reset_index(drop=True)

            # Create the Volcano plot
            figure = dash_bio.VolcanoPlot(
                dataframe=df,
                effect_size='log2FoldChange',
                p='padj', # 'pvalue'
                gene='GeneID',
                snp='GeneID', # Can't seem to remove snp as whenever that happens, throws an error
                genomewideline_value=1.30, #2.5
                genomewideline_width=2,
                effect_size_line=effects,
                effect_size_line_width=2,
                xlabel='log2FoldChange',  # Set x-axis label
                ylabel='-log10(padj)'  # Set y-axis label
            )

            return figure
            
        else:
            # If no data available, return a message or placeholder
            return html.Div("No differential expression data available.", style={'textAlign': 'center'})
