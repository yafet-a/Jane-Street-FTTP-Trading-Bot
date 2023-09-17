# Jane Street FTTP Trading Game Bot - Second Place Finish 🏆

## Overview 📚

Overview for the Python-based trading bot that secured a second-place finish in the Jane Street FTTP Electronic Trading Challenge (ETC). The bot participated in the challenge and successfully executed the below mentioned trading strategies against other competitors' bots on the provided exchange platform.

## Bot Implementation 💻

The bot's implementation is provided in a Python script called `bot.py`. Below are some key components and strategies employed by the bot:

### Configuration ⚙️

Before running the bot, some initial configuration is required. The team name is set at the beginning of the script using the `team_name` variable. Additionally, the script can be run with different parameters to connect to the production exchange or one of the test exchanges.

### Main Loop 🔄

The main trading logic of the bot is executed within the `main` function. Here are the main steps performed by the bot:

1. **Initialisation**: The bot establishes a connection to the exchange and receives an initial "hello" message containing information about its positions.

2. **Trading Strategies**: The bot employs various trading strategies for different symbols traded on the exchange. For example, it calculates fair values for symbols like "VALBZ" and "VALE" based on the top bid and ask prices and decides whether to buy or sell.

3. **Order Management**: The bot manages its orders, including placing new orders, canceling old orders, and tracking unacknowledged orders.

4. **Market Orders**: The bot implements market-making strategies by sending orders slightly more aggressive than the top order on the book.

5. **Position Updates**: The bot updates its positions when "fill" messages are received, reflecting completed trades.

6. **End of Round**: The bot continues trading until a "close" message is received, indicating the end of the round.

### Exchange Connection 🔌

The `ExchangeConnection` class handles the connection to the exchange, sending messages, and reading responses. It also manages order IDs and timestamps to ensure compliance with exchange rate limits.

## How to Run the Bot 🚀

To run the bot, follow these steps:

1. Configure the `team_name` variable with your team's name.

2. Execute the script using the provided instructions in the comments. You may need to change permissions and run the bot in a loop.

```bash
chmod +x bot.py
while true; do ./bot.py --test prod-like; sleep 1; done
