import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from wallet import Wallet
from utils import bcolors, signal_handler
import utils

# Bots
from tradingbot_tendancy import TradingBOT_Tendancy
from tradingbot_dummy_reset import TradingBOT_Dummy_Reset

LAPS = 20

class Simulator:
	"""Simulates the stock context"""
	def __init__(self, bots, typ):
		self.bots = bots
		self.simulation_type = typ

		# Stock simulation
		self.waiting_orders = [[] for b in self.bots]
		self.asks = []
		self.bids = []
		self.txid = 0
		self.order_cancelled = [0 for b in self.bots]
		self.order_passed = [0 for b in self.bots]

		# Instanciate API
		self.cryptowatch = CryptowatchAPI()

	def computeTransaction(self, orders, wallet, b):
		best_ask = self.asks[0][0]
		best_bid = self.bids[0][0]

		for o in orders:
			if o != {}:
				price = o["price"]
				amount = o["amount"]
				o["timestamp"] = time.time()
				o["txid"] = self.txid
				self.txid += 1

				# Determine maker/taker for this order
				o["maker_taker"] = "maker"
				if (o["side"] == "SELL" and price < best_ask) or \
						(o["side"] == "BUY" and price > best_bid):
					o["maker_taker"] = "taker"

				self.waiting_orders[b].append(o)

		# Loop throuh all orders to update
		success = True
		for o in list(self.waiting_orders[b]):
			if time.time() - o["timestamp"] > o["runtime"]:
				# Cancel order
				self.waiting_orders[b].remove(o)
				continue

			price = o["price"]
			amount = o["amount"]
			maker_taker = o["maker_taker"]

			success = False
			if o["side"] == "SELL":
				if o["type"] == "LIMIT" and best_bid > price:
					# Apply order
					success = wallet.convert(amount, price, "ETH_to_EUR", maker_taker) # TODO
					self.waiting_orders[b].remove(o)
				elif o["type"] == "MARKET":
					# Fetch the best bid immediately
					success = wallet.convert(amount, best_bid, "ETH_to_EUR", maker_taker)
					self.waiting_orders[b].remove(o)
			elif o["side"] == "BUY":
				if o["type"] == "LIMIT" and best_ask < price:
					# Apply order
					success = wallet.convert(amount, price, "EUR_to_ETH", maker_taker) # TODO
					self.waiting_orders[b].remove(o)
				elif o["type"] == "MARKET":
					# Fetch the best ask immediately
					success = wallet.convert(amount, best_ask, "EUR_to_ETH", maker_taker)
					self.waiting_orders[b].remove(o)

			if success:
				self.order_passed[b] += 1
		return success

	def cancelOrders(self, cancel_txids, b):
		for o in list(self.waiting_orders[b]):
			if o['txid'] in cancel_txids:
				self.waiting_orders[b].remove(o)
				self.order_cancelled[b] += 1

	# Run simulation
	def run(self):
		# Get initial value
		S = 0

		len_history = 1E99
		if self.simulation_type == "history":
			# Load file into memory
			with open("etheur_history", "r") as f:
				history_samples = f.readlines()
			history_samples = [list(map(float, x.strip().split('\t'))) for x in history_samples]
			len_history = len(history_samples)
			startTime = history_samples[0][0]
			start_price = history_samples[0][2]
		else:
			start_price = self.cryptowatch.getCurrentPrice()
			startTime = time.time()
			T = startTime

		price = start_price
		initial_values = [bot.wallet.getEUR() + bot.wallet.getETH() * price for bot in self.bots]
		initial_wallet_saved_EUR = [bot.wallet.getSavedEUR() for bot in self.bots]
		initial_wallet_saved_ETH = [bot.wallet.getSavedETH() for bot in self.bots]

		while utils.IS_RUNNING and S < len_history:
			# Fetch info
			if self.simulation_type == "history":
				# From file
				self.bids = [[history_samples[S][1],1]]
				price = history_samples[S][2]
				self.asks = [[history_samples[S][3],1]]

				T = history_samples[S][0]
				S += 1
				dt = 13
			elif self.simulation_type == "samples":
				# From the API
				orderbook = self.cryptowatch.getCurrentOrderbook()
				self.asks = orderbook["asks"]
				self.bids = orderbook["bids"]
				price = self.cryptowatch.getCurrentPrice()

				# Increment
				T = time.time()
				S += 1
				dt = self.cryptowatch.getTimeout()
			else:
				exit(0)

			# Common info
			mid_price = abs(self.asks[0][0] + self.bids[0][0]) / 2
			inflation = 100 * ((price - start_price) / start_price)

			if (S % LAPS == 0):
				os.system('clear')
				print("\rBest bid\tPrice   \tBest ask" +\
				bcolors.ENDC + bcolors.BOLD + " ({:.3f} s/S)".format(dt) + bcolors.ENDC)
				print(bcolors.OKGREEN + "{:.4f}".format(self.bids[0][0]) + bcolors.ENDC +\
						bcolors.HEADER + "\t{:.4f}".format(price) + bcolors.ENDC  +\
						bcolors.FAIL + "\t{:.4f}".format(self.asks[0][0]) + bcolors.ENDC)
				print("\rInflation :\t{:.3f}%".format(inflation))
				print("\rTotal time :\t{:1.0f} s ({:1.1f} h)".format(T - startTime, (T - startTime) / 3600))
				print("\n\n\r")

			# Loop through all bots
			for b, bot in enumerate(self.bots):
				# Request the bot action
				orders = bot.getOrders(self.asks, self.bids, price);
				wallet = bot.wallet

				# Cancel orders ?
				self.cancelOrders(bot.getOrdersToCancel(self.waiting_orders[b]), b)

				# Compute transaction by adding the order to the stack
				succeeded = self.computeTransaction(orders, wallet, b)

				# Display
				if (S % LAPS == 0):
					if len(orders) > 0:
						order = orders[-1]
					else:
						order = {}

					value = wallet.getEUR() + wallet.getETH() * price
					percent_from_start = (value - initial_values[b]) / initial_values[b]
					diffEUR = (bot.wallet.getSavedEUR() - initial_wallet_saved_EUR[b])
					diffETH = (bot.wallet.getSavedETH() - initial_wallet_saved_ETH[b]) * price
					gains = (diffETH + diffEUR) / (initial_wallet_saved_EUR[b] + initial_wallet_saved_ETH[b] * price)

					if order != {}:
						act = "{} {}".format(order["side"], order["type"])
						amt = "{:.4f}".format(order["amount"])
						p = "{:.4f}".format(order["price"])
					else:
						act = "IDLE"
						amt = ""
						p = ""

					col = bcolors.OKGREEN
					if percent_from_start < 0.0:
						col = bcolors.FAIL

					colg = bcolors.OKGREEN
					if gains < 0.0:
						colg = bcolors.FAIL

					suc = bcolors.WARNING

					# Display Bot Infos
					print(bcolors.HEADER + bcolors.BOLD + str(bot.name) + bcolors.ENDC)
					print("\rWallet : \t{:.5f} ETH  {:.2f} EUR ".format(wallet.getETH(), wallet.getEUR()) +\
							colg + "({:.3f}% savings)".format(gains) + bcolors.ENDC)
					print("\rValue : \t{:.2f} EUR".format(value) + col + "  ({:.3f}%)".format(percent_from_start * 100) + bcolors.ENDC)
					print("\rPass/Cancel :\t{:1.0f} / {:1.0f}".format(self.order_passed[b], self.order_cancelled[b]))
					print("\rNew order : \t" + suc + "{} Price {} ETH Amt. {} ETH".format(act, p, amt) + bcolors.ENDC)
					print("\nWaiting orders")
					# Print last orders
					l = len(self.waiting_orders[b])
					for i in range(min(10, l)):
						s = self.waiting_orders[b][i]
						print("\r\t" + bcolors.OKBLUE + "{} {} {:.4f} ETH".format(s["side"], s["type"], s["price"]) + bcolors.ENDC)
					if(l > 10):
						print("\r\t" + bcolors.OKBLUE + "..." + bcolors.ENDC)

			# time.sleep(0.8)
			if self.simulation_type != "history":
				# Sleep a bit
				time.sleep(dt)

if __name__ == '__main__':
	# Bind Ctrl-C signal
	signal.signal(signal.SIGINT, signal_handler)

	# Request number of samples or time
	if len(sys.argv) < 4:
		print("Wrong input. Format is : samples/history ETH EUR")
		exit(0)

	typ = sys.argv[1]
	ETH_amount = float(sys.argv[2])
	EUR_amout = float(sys.argv[3])

	# Init bots
	if typ == "history":
		with open("etheur_history", "r") as f:
			H = f.readline()
			H = list(map(float, H.strip().split('\t')))
			price = H[2]
	else:
		price = CryptowatchAPI().getCurrentPrice()
	B = [TradingBOT_Dummy_Reset(Wallet(ETH_amount, EUR_amout), price),
		TradingBOT_Tendancy(Wallet(ETH_amount, EUR_amout), price)]

	# Launch simulation
	S = Simulator(B, typ)
	S.run()
