import os 
import os.path as op


def get_files(path, ext=None):
    """Collect file names from a folder, accordingly with their extension

    Args:
        path (str): The path to the folder containing the files.
        ext (str, optional): The file extension to filter by. Defaults to None.

    Returns:
        list: A list of file paths that match the criteria.
    """
    files = []
    for f in os.listdir(path):
        if ext is None or f.endswith(ext):
            files.append(op.join(path, f))
    return files
