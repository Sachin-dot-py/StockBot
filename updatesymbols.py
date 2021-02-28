import json
import requests
if __name__ == "__main__":
    with open('symbols.json', 'w') as outfile:
        json.dump(requests.get('https://api.iextrading.com/1.0/ref-data/symbols').json(), outfile)
