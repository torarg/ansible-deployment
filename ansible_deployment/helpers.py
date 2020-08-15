import pickle

def save_object(obj, file_path):
    with open(file_path, 'wb') as file_stream:
        pickle.dump(obj, file_stream)

def load_object(file_path):
    with open(file_path, 'rb') as file_stream:
        return pickle.load(file_stream)
