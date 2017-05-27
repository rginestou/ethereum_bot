import os, sys
import time

from cryptowatchapi import CryptowatchAPI

if __name__ == '__main__':
	cryptowatch = CryptowatchAPI()
	start_time = time.time()

	with open("etheur_history", "a") as f:
		while True:
			price = cryptowatch.getCurrentPrice()
			orderbook = cryptowatch.getCurrentOrderbook()
			asks = orderbook["asks"]
			bids = orderbook["bids"]
			best_bid = bids[0][0]
			best_ask = asks[0][0]
			timestamp = time.time()

			f.write("{:1.0f}\t{:.5f}\t{:.5f}\t{:.5f}\n".format(time.time(), best_bid, price, best_ask))

			sys.stdout.write("\rCompleted {:1.0f} seconds of history...".format(timestamp - start_time))
			sys.stdout.flush()

			# Wait 10 sec
			time.sleep(10)
