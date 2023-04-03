#!/usr/bin/env python3
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py --test prod-like; sleep 1; done

import argparse
import json
import socket
import time
from collections import deque
from enum import Enum

# ~~~~~============== CONFIGURATION  ==============~~~~~
# Replace "REPLACEME" with your team name!
team_name = "GRACEYAFIT"


def update_positions(positions, message):
    if message["dir"] == "BUY":
        sign = 1
    else:
        sign = -1

    symbol = message["symbol"]
    if symbol in positions:
        old_position = positions[symbol]
    else:
        old_position = 0
    positions[symbol] = old_position + (sign * message["size"])


# ~~~~~============== MAIN LOOP ==============~~~~~

# You should put your code here! We've provided some starter code as an example. For now,
# you should jump straight to "STEP 1" below, but once you get to "STEP 3", you should
# feel free to change/remove/edit/update any of the starter code as you'd like. If you
# have any questions about the starter code, please ask us!


def main():
    args = parse_arguments()
    exchange = ExchangeConnection(args=args)

    # Store and print the "hello" message received from the exchange. This
    # contains useful information about your positions. Normally you start with
    # all positions at zero, but if you reconnect during a round, you might
    # have already bought/sold symbols and have non-zero positions.
    hello_message = exchange.read_message()
    print("First message from exchange:", hello_message)

    # Dict from symbol -> position
    positions = {}
    # The exchange tells us our initial positions when we start up - in case we start up
    # in the middle of a round - so we record them here
    for single_position in hello_message["symbols"]:
        positions[single_position["symbol"]] = single_position["position"]

    # Dict from symbol to timestamp
    # TODO: Uncomment this in STEP 2
    last_providing_order_sent = {}

    # Dicts from order_id -> symbol
    unacked_orders_by_id = {}
    open_orders_by_id = {}

    # Dict from symbol -> set of open order_ids
    open_orders_by_symbol = {}

    # Here is the main loop of the program. It will continue to read and process
    # messages in a loop until a "close" message is received.  Feel free to modify any
    # of the starter code below, once you've finished steps 1 and 2.
    #
    # Note: a common mistake people make is to call write_message() at least once for
    # every read_message() response.
    #
    # Every message sent to the exchange generates at least one response message.
    # Sending a message in response to every exchange message will cause a feedback loop
    # where your bot's messages will quickly be rate-limited and ignored. Please, don't
    # do that!

    def trade(message, fair_value, symbol):
        if "buy" in message and len(message["buy"]) > 0:
            bid_price, bid_size = message["buy"][0]
        else:
            bid_price, bid_size = None, None
        if "sell" in message and len(message["sell"]) > 0:
            ask_price, ask_size = message["sell"][0]
        else:
            ask_price, ask_size = None, None

        if bid_price is not None and bid_price > fair_value:
            # If someone is trying to buy for more than our fair value, let's
            # sell to them
            id = exchange.send_add_message(symbol, "SELL", bid_price, bid_size)
            unacked_orders_by_id[id] = symbol
        elif ask_price is not None and ask_price < fair_value:
            # If someone is trying to sell for less than our fair value, let's
            # buy from them
            id = exchange.send_add_message(symbol, "BUY", ask_price, ask_size)
            unacked_orders_by_id[id] = symbol
        else:

            # The bid price is less than the fair value, and the ask
            # price is more, so we don't want to trade with any open
            # orders. Instead, let's "penny" them, i.e. send an order that is
            # slightly more "aggressive" than the top order on the book. We don't want to do this on every book message, as per
            # the comment above, so let's only do it if it's been 0.05s
            # since the last order we sent.
        
            now = time.time()
            seconds_since_last_providing_order_sent = (
                now - last_providing_order_sent.get(symbol, 0)
            )
            if seconds_since_last_providing_order_sent > 0.01:
                last_providing_order_sent[symbol] = now

                # Cancel our old orders before sending new ones
                if symbol in open_orders_by_symbol:
                    for order_id in open_orders_by_symbol[symbol]:
                        exchange.send_cancel_message(order_id)

                # Send some new orders
                if bid_price is None:
                    my_bid_price = 0.99 * fair_value
                else:
                    y = bid_price * 1.02
                    my_bid_price = y if y < fair_value else bid_price
                id = exchange.send_add_message(symbol, "BUY", my_bid_price, bid_size)
                unacked_orders_by_id[id] = symbol

                if ask_price is None:
                    my_ask_price = 1.01*fair_value
                else:
                    x = 0.988 * ask_price
                    my_ask_price = x if x > fair_value else ask_price 
                id = exchange.send_add_message(symbol, "SELL", my_ask_price, ask_size)
                unacked_orders_by_id[id] = symbol
    
    valbz_fair_value = None
    # gs_fair_value = None
    # ms_fair_value = None
    xlf_fair_value = None
    # wfc_fair_value = None


    while True:
        
        message = exchange.read_message()
        # Some of the message types below happen infrequently and contain
        # important information to help you understand what your bot is doing,
        # so they are printed in full. We recommend not always printing every
        # message because it can be a lot of information to read. Instead, let
        # your code handle the messages and just print the information
        # important for you!
        if message["type"] == "close":
            print("The round has ended")
            break
        elif message["type"] == "error":
            print(message)
        elif message["type"] == "reject":
            del unacked_orders_by_id[message["order_id"]]
            print(message)
        elif message["type"] == "fill":
            update_positions(positions, message)
        elif message["type"] == "book":
            symbol = message["symbol"]
            
            #BOND
            if symbol == "BOND":
                trade(message, 1000, symbol)  
            
            #VALBZ & VALE STRATEGY
            
            if symbol == "VALBZ":
                if len(message["buy"]) > 0 and len(message["sell"]) > 0:
                    valbz_fair_value = (message["buy"][0][0] + message["sell"][0][0]) * 0.5
            
            if symbol == "VALE":
                if valbz_fair_value != None: 
                    trade(message, valbz_fair_value, symbol)

            #GS, MS, WFC

            # if symbol == "GS":
            #     if len(message["buy"]) > 0 and len(message["sell"]) > 0:
            #         gs_fair_value = (message["buy"][0][0] + message["sell"][0][0]) * 0.5
            #         trade(message, gs_fair_value, symbol)

            # if symbol == "MS":
            #     if len(message["buy"]) > 0 and len(message["sell"]) > 0:
            #         ms_fair_value = (message["buy"][0][0] + message["sell"][0][0]) * 0.5
            #         trade(message, ms_fair_value, symbol)

            if symbol == "XLF":
                if len(message["buy"]) > 0 and len(message["sell"]) > 0:
                    xlf_fair_value = (message["buy"][0][0] + message["sell"][0][0]) * 0.5
                    trade(message, xlf_fair_value, symbol)
            
            # if symbol == "WFC":
            #     if len(message["buy"]) > 0 and len(message["sell"]) > 0:
            #         wfc_fair_value = (message["buy"][0][0] + message["sell"][0][0]) * 0.5
            #         trade(message, wfc_fair_value, symbol)

        elif message["type"] == "out":
            # Update open_orders_by_symbol and open_orders_by_id
            order_id = message["order_id"]
            symbol = open_orders_by_id[order_id]

            del open_orders_by_id[order_id]
            open_orders_by_symbol[symbol].remove(order_id)

        elif message["type"] == "ack":
            # Update our open_orders_* dictionaries, as well as unacked_orders_by_id
            order_id = message["order_id"]
            symbol = unacked_orders_by_id[order_id]
            del unacked_orders_by_id[order_id]

            if symbol in open_orders_by_symbol:
                open_orders = open_orders_by_symbol[symbol]
            else:
                open_orders = set()
            open_orders.add(order_id)
            open_orders_by_symbol[symbol] = open_orders
            open_orders_by_id[order_id] = symbol


# ~~~~~============== PROVIDED CODE ==============~~~~~

# You probably don't need to edit anything below this line, but feel free to
# ask if you have any questions about what it is doing or how it works. If you
# do need to change anything below this line, please feel free to


class Dir(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExchangeConnection:
    def __init__(self, args):
        self.message_timestamps = deque(maxlen=500)
        self.order_id = 1
        self.exchange_hostname = args.exchange_hostname
        self.port = args.port
        exchange_socket = self._connect(add_socket_timeout=args.add_socket_timeout)
        self.reader = exchange_socket.makefile("r", 1)
        self.writer = exchange_socket

        self._write_message({"type": "hello", "team": team_name.upper()})

    def read_message(self):
        """Read a single message from the exchange"""
        message = json.loads(self.reader.readline())
        if "dir" in message:
            message["dir"] = Dir(message["dir"])
        return message

    def send_add_message(self, symbol: str, dir: Dir, price: int, size: int):

        """Add a new order"""
        self._write_message(
            {
                "type": "add",
                "order_id": self.order_id,
                "symbol": symbol,
                "dir": dir,
                "price": price,
                "size": size,
            }
        )
        order_id = self.order_id
        self.order_id += 1
        return order_id

    def send_convert_message(self, order_id: int, symbol: str, dir: Dir, size: int):
        """Convert between related symbols"""
        self._write_message(
            {
                "type": "convert",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "size": size,
            }
        )

    def send_cancel_message(self, order_id: int):
        """Cancel an existing order"""
        self._write_message({"type": "cancel", "order_id": order_id})

    def _connect(self, add_socket_timeout):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if add_socket_timeout:
            # Automatically raise an exception if no data has been recieved for
            # multiple seconds. This should not be enabled on an "empty" test
            # exchange.
            s.settimeout(5)
        s.connect((self.exchange_hostname, self.port))
        return s

    def _write_message(self, message):
        what_to_write = json.dumps(message)
        if not what_to_write.endswith("\n"):
            what_to_write = what_to_write + "\n"

        length_to_send = len(what_to_write)
        total_sent = 0
        while total_sent < length_to_send:
            sent_this_time = self.writer.send(
                what_to_write[total_sent:].encode("utf-8")
            )
            if sent_this_time == 0:
                raise Exception("Unable to send data to exchange")
            total_sent += sent_this_time

        now = time.time()
        self.message_timestamps.append(now)
        if len(
            self.message_timestamps
        ) == self.message_timestamps.maxlen and self.message_timestamps[0] > (now - 1):
            print(
                "WARNING: You are sending messages too frequently. The exchange will start ignoring your messages. Make sure you are not sending a message in response to every exchange message."
            )


def parse_arguments():
    test_exchange_port_offsets = {"prod-like": 0, "slower": 1, "empty": 2}

    parser = argparse.ArgumentParser(description="Trade on an ETC exchange!")
    exchange_address_group = parser.add_mutually_exclusive_group(required=True)
    exchange_address_group.add_argument(
        "--production", action="store_true", help="Connect to the production exchange."
    )
    exchange_address_group.add_argument(
        "--test",
        type=str,
        choices=test_exchange_port_offsets.keys(),
        help="Connect to a test exchange.",
    )

    # Connect to a specific host. This is only intended to be used for debugging.
    exchange_address_group.add_argument(
        "--specific-address", type=str, metavar="HOST:PORT", help=argparse.SUPPRESS
    )

    args = parser.parse_args()
    args.add_socket_timeout = True

    if args.production:
        args.exchange_hostname = "production"
        args.port = 25000
    elif args.test:
        args.exchange_hostname = "test-exch-" + team_name
        args.port = 25000 + test_exchange_port_offsets[args.test]
        if args.test == "empty":
            args.add_socket_timeout = False
    elif args.specific_address:
        args.exchange_hostname, port = args.specific_address.split(":")
        args.port = int(port)

    return args


if __name__ == "__main__":
    # Check that [team_name] has been updated.
    assert (
        team_name != "REPLACEME"
    ), "Please put your team name in the variable [team_name]."

    main()

