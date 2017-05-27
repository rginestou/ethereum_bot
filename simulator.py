import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from wallet import Wallet
from tradingbot_dummy import TradingBOT_Dummy
from tradingbot_dummy_reset import TradingBOT_Dummy_Reset
from utils import bcolors, signal_handler
import utils

class Simulator:
	"""Simulates the stock context"""
	def __init__(self, bots, typ, val):
		self.bots = bots
		self.simulation_type = typ
		self.simulation_value = val

		# Stock simulation
		self.waiting_orders = [[] for b in self.bots]
		self.asks = []
		self.bids = []

		# Instanciate API
		self.cryptowatch = CryptowatchAPI()

	def computeTransaction(self, order, wallet, b):
		best_ask = self.asks[0][0]
		best_bid = self.bids[0][0]

		if order != {}:
			price = order["price"]
			amount = order["amount"]
			order["timestamp"] = time.time()

			# Determine maker/taker for this order
			order["maker_taker"] = "maker"
			if (order["side"] == "SELL" and price < best_ask) or \
					(order["side"] == "BUY" and price > best_bid):
				order["maker_taker"] = "taker"

			self.waiting_orders[b].append(order)

		success = True
		# Loop throuh all orders to update
		for o in list(self.waiting_orders[b]):
			if time.time() - o["timestamp"] > o["runtime"]:
				# Cancel order
				self.waiting_orders[b].remove(o)
				continue

			price = o["price"]
			amount = o["amount"]
			maker_taker = o["maker_taker"]

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
					self.waiting_orders.remove(o)

		return success

	# Run simulation
	def run(self):
		# Get initial value
		price = self.cryptowatch.getCurrentPrice()
		initial_values = [bot.wallet.getEUR() + bot.wallet.getETH() * price for bot in self.bots]

		# Run
		startTime = time.time()
		T = startTime
		S = 0
		while utils.IS_RUNNING and ((typ == 'time' and T - startTime < val) or (typ == 'samples' and S < val)):
			# Fetch info
			orderbook = self.cryptowatch.getCurrentOrderbook()
			self.asks = orderbook["asks"]
			self.bids = orderbook["bids"]
			mid_price = abs(self.asks[0][0] + self.bids[0][0]) / 2
			price = self.cryptowatch.getCurrentPrice()

			# Increment
			T = time.time()
			S += 1
			dt = self.cryptowatch.getTimeout()

			# Common info
			os.system('clear')
			print("\rBest bid\tPrice\tBest ask" +\
			bcolors.ENDC + bcolors.BOLD + " ({:.3f} S/s)".format(1.0 / dt) + bcolors.ENDC)
			print(bcolors.OKGREEN + "{:.4f}".format(self.bids[0][0]) + bcolors.ENDC +\
					bcolors.HEADER + "\t{:.4f}".format(price) + bcolors.ENDC  +\
					bcolors.FAIL + "\t{:.4f}".format(self.asks[0][0]) + bcolors.ENDC)
			print("\rTotal time :\t{:1.0f} s".format(T - startTime))
			print("\n\n\r")

			# Loop through all bots
			for b, bot in enumerate(self.bots):
				# Request the bot action
				order = bot.getOrder(self.asks, self.bids, price);
				wallet = bot.wallet

				# Compute transaction by adding the order to the stack
				succeeded = self.computeTransaction(order, wallet, b)

				# Display
				value = wallet.getEUR() + wallet.getETH() * mid_price
				percent_from_start = (value - initial_values[b]) / initial_values[b]

				if order != {}:
					act = "{} {}".format(order["side"], order["type"])
					amt = "{:.4f}".format(order["amount"])
					price = "{:.4f}".format(order["price"])
				else:
					act = "IDLE"
					amt = ""
					price = ""

				col = bcolors.OKGREEN
				if percent_from_start < 0.0:
					col = bcolors.FAIL

				suc = bcolors.OKBLUE
				if not succeeded:
					suc = bcolors.WARNING

				# Display Bot Infos
				print(bcolors.HEADER + bcolors.BOLD + str(bot.name) + bcolors.ENDC)
				print("\rWallet : \t{:.5f} ETH  {:.2f} EUR".format(wallet.getETH(), wallet.getEUR()))
				print("\rValue : \t{:.2f} EUR".format(value) + col + "  ({:.3f}%)".format(percent_from_start * 100) + bcolors.ENDC)
				print("\rNew order : \t" + suc + "{} Price {} ETH Amt. {} ETH".format(act, price, amt) + bcolors.ENDC)
				print("\nWaiting orders")
				for s in self.waiting_orders[b]:
					print("\r\t" + bcolors.OKBLUE + "{} {} {} ETH".format(s["side"], s["type"], price) + bcolors.ENDC)

			# Sleep a bit
			time.sleep(dt)

if __name__ == '__main__':
	# Bind Ctrl-C signal
	signal.signal(signal.SIGINT, signal_handler)

	# Request number of samples or time
	if len(sys.argv) < 5:
		print("Wrong input. Format is : time/samples value(seconds/samples) ETH EUR")
		exit(0)

	typ = sys.argv[1]
	val = int(sys.argv[2])
	ETH_amount = float(sys.argv[3])
	EUR_amout = float(sys.argv[4])

	# Forever
	if val < 0:
		val = 1E99

	# Init bots
	price = CryptowatchAPI().getCurrentPrice()
	B = [TradingBOT_Dummy_Reset(Wallet(ETH_amount, EUR_amout), price)]

	# Launch simulation
	S = Simulator(B, typ, val)
	S.run()
