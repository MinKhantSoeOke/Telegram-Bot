import os
from dotenv import load_dotenv
import telebot
import yfinance as yf
import requests

load_dotenv()

API_KEY = os.getenv('API_KEY')

if not API_KEY:
    raise ValueError("No API key found. Please set the API_KEY environment variable.")

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['Greet'])
def greet(message):
    bot.reply_to(message, "Hey! How is it going?")

@bot.message_handler(commands=['hello'])
def hello(message):
    bot.send_message(message.chat.id, "Hello!")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "/Greet - Greet the bot\n"
        "/hello - Say hello\n"
        "/wsb - Get stock prices\n"
        "/price [ticker] - Get stock price for a specific ticker\n"
        "/crypto [symbol] - Get cryptocurrency price\n"
        "/joke - Get a random joke\n"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['wsb'])
def get_stocks(message):
    response = ""
    stocks = ['gme', 'amc', 'nok']
    stock_data = []

    for stock in stocks:
        try:
            data = yf.download(tickers=stock, period='5d', interval='1d')
            data = data.reset_index()
            response += f"-----{stock.upper()}-----\n"

            stock_prices = [stock]
            columns = ['stock']
            for index, row in data.iterrows():
                price = round(row['Close'], 2)
                format_date = row['Date'].strftime('%m/%d')
                response += f"{format_date}: {price}\n"
                stock_prices.append(price)
                columns.append(format_date)
            
            stock_data.append(stock_prices)
        except Exception as e:
            response += f"Failed to download data for {stock}: {e}\n"
    
    response = f"{columns[0] : <10}{columns[1] : ^10}{columns[2] : ^10}{columns[3] : ^10}{columns[4] : ^10}{columns[5] : ^10}\n"
    for row in stock_data:
        response += f"{row[0] : <10}{row[1] : ^10}{row[2] : ^10}{row[3] : ^10}{row[4] : ^10}{row[5] : ^10}\n"
    response += "\nStock Data"
    bot.send_message(message.chat.id, response)

def stock_request(message):
    request = message.text.split()
    if len(request) < 2 or request[0].lower() not in "price":
        return False
    else:
        return True
    
@bot.message_handler(func=stock_request)
def send_price(message):
    request = message.text.split()[1]
    try:
        data = yf.download(tickers=request, period='1d', interval='1m')
        if data.size > 0:
            data = data.reset_index()
            data["format_date"] = data["Datetime"].dt.strftime('%m/%d %I:%M %p')
            data.set_index('format_date', inplace=True)
            print(data.to_string())
            bot.send_message(message.chat.id, data['Close'].to_string(header=False))
        else:
            bot.send_message(message.chat.id, "No data found for the given ticker.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error retrieving data: {e}")

@bot.message_handler(commands=['crypto'])
def get_crypto_price(message):
    try:
        command, crypto_symbol = message.text.split(maxsplit=1)
        crypto_symbol = crypto_symbol.upper()

        name_to_symbol = {
            'BITCOIN': 'BTC',
            'ETHEREUM': 'ETH',
            'RIPPLE': 'XRP',
            'LITECOIN': 'LTC',
            'CARDANO': 'ADA',
            'POLKADOT': 'DOT',
            'CHAINLINK': 'LINK',
            'STELLAR': 'XLM',
            'DOGECOIN': 'DOGE',
            'UNISWAP': 'UNI',
            'AAVE': 'AAVE',
            'MONERO': 'XMR',
            'BITCOIN CASH': 'BCH',
            'BINANCE COIN': 'BNB',
            'SOLANA': 'SOL',
            'TETHER': 'USDT',
            'USD COIN': 'USDC',
            'WRAPPED BITCOIN': 'WBTC',
            'EOS': 'EOS',
            'TEZOS': 'XTZ',
        }

        # Check if the provided name is in the mapping dictionary
        crypto_symbol = name_to_symbol.get(crypto_symbol, crypto_symbol)

        api_key = os.getenv('api_key')
        if not api_key:
            raise ValueError("No CoinMarketCap API key found. Please set the COINMARKETCAP_API_KEY environment variable.")

        base_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {'symbol': crypto_symbol}
        headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': api_key}

        response = requests.get(base_url, headers=headers, params=parameters)
        data = response.json()

        # Check the response status
        if data.get("status") and data["status"]["error_code"] == 0:
            # Get the price and send it to the user
            price = data["data"][crypto_symbol]["quote"]["USD"]["price"]
            response_message = f"The current price of {crypto_symbol} is ${price:.2f} USD."
        else:
            error_message = data["status"]["error_message"]
            response_message = f"Cryptocurrency not found or error occurred: {error_message}"
    except IndexError:
        response_message = "Please provide a cryptocurrency symbol after the /crypto command."
    except ValueError as ve:
        response_message = str(ve)
    except Exception as e:
        response_message = f"An error occurred: {e}"

    bot.send_message(message.chat.id, response_message)

@bot.message_handler(commands=['joke'])
def get_joke(message):
    try:
        response = requests.get("https://official-joke-api.appspot.com/random_joke")
        joke = response.json()
        response_message = f"{joke['setup']} {joke['punchline']}"
    except Exception as e:
        response_message = f"An error occurred while fetching a joke: {e}"
    
    bot.send_message(message.chat.id, response_message)


@bot.message_handler(func=lambda message: True)
def handle_all_other_messages(message):
    bot.send_message(message.chat.id, "I'm sorry, I don't understand that command. Type /help to see the list of available commands.")

bot.polling()
