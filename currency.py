import loggingconfig
from credentials import currency_api_key
import requests

def getRate():
    req = requests.get(f"http://data.fixer.io/api/latest?symbols=SGD,USD&access_key={currency_api_key}").json()
    EURSGD = float(req['rates']['SGD'])
    EURUSD = float(req['rates']['USD'])
    USDSGD = round(EURSGD/EURUSD,2)
    return USDSGD

if __name__ == '__main__':
    rate = getRate()
    with open("currency.txt", "w") as f:
        f.write(str(rate))