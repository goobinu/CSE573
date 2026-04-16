import csv

def save_to_csv(file_path, headers, data):
    """
    Saves a list of data to a CSV file.
    
    Args:
        file_path (str): The path to the CSV file.
        headers (list): A list of strings representing the column headers.
        data (list): A list of lists or tuples containing the data to save.
    """
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)

def read_from_csv(file_path):
    """
    Reads data from a CSV file.
    
    Args:
        file_path (str): The path to the CSV file.
        
    Returns:
        list: A list of lists representing the rows in the CSV file.
    """
    with open(file_path, mode='r') as f:
        reader = csv.reader(f)
        return list(reader)

def read_column_from_csv(file_path, column_index, skip_header=False):
    """
    Reads a specific column from a CSV file.
    
    Args:
        file_path (str): The path to the CSV file.
        column_index (int): The index of the column to retrieve.
        skip_header (bool): Whether to skip the first row (header). Defaults to False.
        
    Returns:
        list: A list of values from the specified column.
    """
    results = []
    with open(file_path, mode='r') as f:
        reader = csv.reader(f)
        if skip_header:
            next(reader, None)
        for row in reader:
            if len(row) > column_index:
                results.append(row[column_index])
    return results