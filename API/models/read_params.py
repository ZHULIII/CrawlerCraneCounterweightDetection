import json
def read_params(path='params.txt'):
    with open(path, "r", encoding="utf-8") as f:
        params = json.load(f)
    return params
