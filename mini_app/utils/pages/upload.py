from dash import callback, Input,  Output, State
from dash.exceptions import PreventUpdate
import numpy as np

from utils.helper_functions.main_functions import *

def upload_functions():

    def validate_gene_count_format(df):
        """
        Validate if the uploaded file is in the correct gene count table format
        Customize this function based on your specific requirements
        """
        try:
            # Check if dataframe is not empty
            if df.empty:
                return False
            
            # Check if first column contains gene names/IDs (should be strings)
            if not df.iloc[:, 0].dtype == 'object':
                return False
            
            # Check if other columns contain numeric data (gene counts)
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) < 1:
                return False
            
            # Check for negative values in count data (counts should be non-negative)
            numeric_data = df.select_dtypes(include=[np.number])
            if (numeric_data < 0).any().any():
                return False
            
            # Add more specific validation rules based on your gene count table requirements
            # For example:
            # - Minimum number of samples required
            # - Specific column naming conventions
            # - Gene ID format validation
            
            return True
            
        except Exception:
            return False

    # Single callback for processing the file and updating all outputs
    @callback(
        [Output('gc-filestorage', 'data'),
         Output('filename-display', 'children'),
         Output('upload-error-alert', 'children'),
         Output('upload-error-alert', 'is_open')],
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')]
    )
    def update_output(list_of_contents, filenames):
        try:
            # Check if contents are not empty
            if list_of_contents is not None and filenames is not None:
                # Get the first item from the list  
                contents = list_of_contents[0] if isinstance(list_of_contents, list) else list_of_contents
                filename = filenames[0] if isinstance(filenames, list) else filenames

                # Decode the uploaded file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                # Check file extension
                if filename.endswith('.csv'):
                    try:
                        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                    except UnicodeDecodeError:
                        df = pd.read_csv(io.StringIO(decoded.decode('latin-1')))
                elif filename.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(io.BytesIO(decoded))
                else:
                    # Wrong file format
                    error_msg = f"Wrong format: {filename}. Please upload a CSV or Excel file."
                    return None, "", error_msg, True
                
                # Validate gene count table format
                if not validate_gene_count_format(df):
                    error_msg = "The format of gene count table is not supported. Please check your file format."
                    return None, "", error_msg, True
                
                # If validation passes, store the data
                filename_string = f'The uploaded file is {filename}'
                return df.to_json(date_format='iso', orient='split'), filename_string, "", False
                
            else:
                # Return empty data and columns if no file is uploaded
                return None, "No file uploaded.", "", False
        
        except Exception as e:
            filename_string = f'An error occurred with the uploaded file "{filenames}". Check the file and make sure that a gene count table is uploaded.'
            error_msg = "The format of gene count table is not supported. Please check your file format."
            return None, filename_string, error_msg, True