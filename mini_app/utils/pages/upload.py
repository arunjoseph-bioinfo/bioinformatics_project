from dash import callback, Input,  Output, State

from utils.helper_functions.main_functions import *

def upload_functions():
    # Callback for processing the file and updating the table
    @callback(
        [Output('gc-filestorage', 'data'),
        Output('filename-display', 'children')],
        [Input('upload-data', 'contents'),
        State('upload-data', 'filename')]
    )
    def update_output(list_of_contents, filenames):
        try:
            # Check if contents are not empty
            if list_of_contents is not None and filenames is not None:
                # Get the first item from the list  
                contents = list_of_contents[0]
                filename = filenames[0]

                filename_string = f'The uploaded file is {filename}'

                # Parse the contents of the file
                df, error = parse_contents(contents)

                # Displays the error in file upload
                if error:
                    filename_string = f'The format of the uploaded file "{filename}" is not supported.'
                    return [], [], None, filename_string, None
                
                else:
                    # Update the table data and columns
                    return df.to_json(date_format='iso', orient='split'), filename_string
            else:
                # Return empty data and columns if no file is uploaded
                return None, "No file uploaded."
        
        except Exception as e:

            filename_string = f'An error occurred with the uploaded file "{filename}". Check the file and make sure that a gene count table is uploaded.'

            return None, filename_string