import pickle
import sys

def save_object(obj, file_path):
    with open(file_path, 'wb') as file_stream:
        pickle.dump(obj, file_stream)

def load_object(file_path):
    if not file_path.exists():
        print("Error: {} not found.".format(file_path))
        sys.exit()
    with open(file_path, 'rb') as file_stream:
        return pickle.load(file_stream)
