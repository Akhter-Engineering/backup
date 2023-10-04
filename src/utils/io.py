import os

def delete_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
