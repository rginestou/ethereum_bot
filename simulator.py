import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from wallet import Wallet
from utils import tc, signal_handler
import utils

# Bots
from tradingbot_tendancy import TradingBOT_Tendancy
from tradingbot_dummy_reset import TradingBOT_Dummy_Reset
from tradingbot_manual import TradingBOT_Manual

LAPS = 200

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

	def computeTransaction(self, asks, bids, orders, wallet, b, current_time):
		best_ask = asks[0][0]
		best_bid = bids[0][0]

		for o in orders:
			if o == {}:
				continue

			price = o["price"]
			amount = o["amount"]
			o["timestamp"] = current_time
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
			if current_time - o["timestamp"] > o["runtime"]:
				# Cancel order
				self.waiting_orders[b].remove(o)
				continue

			price = o["price"]
			amount = o["amount"]
			maker_taker = o["maker_taker"]

			success = False
			if o["side"] == "SELL":
				if o["type"] == "LIMIT" and best_bid >= price:
					# Apply order
					success = wallet.convert(amount, price, "ETH_to_EUR", maker_taker)
					self.waiting_orders[b].remove(o)
				elif o["type"] == "MARKET":
					# Fetch the best bid immediately
					success = wallet.convert(amount, best_bid, "ETH_to_EUR", maker_taker)
					self.waiting_orders[b].remove(o)
			elif o["side"] == "BUY":
				if o["type"] == "LIMIT" and best_ask <= price:
					# Apply order
					success = wallet.convert(amount, price, "EUR_to_ETH", maker_taker)
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
		iter_n = 0

		len_history = 1E99
		if self.simulation_type == "history":
			# Load file into memory
			with open("etheur_history", "r") as f:
				history_samples = f.readlines()
			history_samples = [list(map(float, x.strip().split('\t'))) for x in history_samples]

			len_history = len(history_samples)
			self.start_time = history_samples[0][0]
			self.start_price = history_samples[0][2]
		else:
			# Initiate from API
			self.start_price = self.cryptowatch.getCurrentPrice()
			self.start_time = time.time()
			T = start_time

		# Initial values for comparison
		price = self.start_price
		self.initial_values = [bot.wallet.getEUR() + bot.wallet.getETH() * price for bot in self.bots]
		self.initial_wallet_saved_EUR = [bot.wallet.getSavedEUR() for bot in self.bots]
		self.initial_wallet_saved_ETH = [bot.wallet.getSavedETH() for bot in self.bots]

		# Main loop
		while utils.IS_RUNNING and iter_n < len_history:
			# Fetch info
			if self.simulation_type == "history":
				# From file
				bids = [[history_samples[iter_n][1],1]]
				price = history_samples[iter_n][2]
				asks = [[history_samples[iter_n][3],1]]

				T = history_samples[iter_n][0]
				iter_n += 1
				dt = 13
			elif self.simulation_type == "samples":
				# From the API
				orderbook = self.cryptowatch.getCurrentOrderbook()
				asks = orderbook["asks"]
				bids = orderbook["bids"]
				price = self.cryptowatch.getCurrentPrice()

				# Increment
				T = time.time()
				iter_n += 1
				dt = self.cryptowatch.getTimeout()
			else:
				exit(0)

			# Display simulator info
			if iter_n % LAPS == 0 or iter_n == len_history:
				self.displaySimulationInfo(asks, bids, price, iter_n, T, dt)

			# Loop through all bots
			for b, bot in enumerate(self.bots):
				# Request the bot action
				orders = bot.getOrders(asks, bids, price);
				wallet = bot.wallet

				# Compute transaction by adding the order to the stack
				succeeded = self.computeTransaction(asks, bids, orders, wallet, b, T)

				# Cancel orders ?
				self.cancelOrders(bot.getOrdersToCancel(self.waiting_orders[b]), b)

				# Display bot info
				if iter_n % LAPS == 0 or iter_n == len_history:
					self.displayBotInfo(b, bot, orders, wallet, price, iter_n)

			# Wait for the next round if in real time mode
			if self.simulation_type != "history":
				# Sleep a bit
				time.sleep(dt)

		# Display final info
		self.displayFinalBotsInfo()

	def displaySimulationInfo(self, asks, bids, price, iter_n, T, dt):
		# Common info
		inflation = 100 * ((price - self.start_price) / self.start_price)

		os.system('clear')
		print("\rBest bid\tPrice   \tBest ask" +\
				tc.ENDC + tc.BOLD + " ({:.3f} s/S)".format(dt) + tc.ENDC)
		print(tc.OKGREEN + "{:.4f}".format(bids[0][0]) + tc.ENDC +\
				tc.HEADER + "\t{:.4f}".format(price) + tc.ENDC  +\
				tc.FAIL + "\t{:.4f}".format(asks[0][0]) + tc.ENDC)
		print("\rInflation :\t{:.3f}%".format(inflation))
		print("\rTotal time :\t{:1.0f} s ({:1.1f} h)".format(T - self.start_time, (T - self.start_time) / 3600))
		print("\n\r")

	def displayBotInfo(self, bot_id, bot, orders, wallet, price, iter_n):
		if len(orders) > 0:
			order = orders[-1]
		else:
			order = {}

		value = wallet.getEUR() + wallet.getETH() * price
		percent_from_start = (value - self.initial_values[bot_id]) / self.initial_values[bot_id]
		diffEUR = (wallet.getSavedEUR() - self.initial_wallet_saved_EUR[bot_id])
		diffETH = (wallet.getSavedETH() - self.initial_wallet_saved_ETH[bot_id]) * price
		gains = (diffETH + diffEUR) / (self.initial_wallet_saved_EUR[bot_id] + self.initial_wallet_saved_ETH[bot_id] * price)
		gains_no_inflation = (diffETH / price * self.start_price + diffEUR) / (self.initial_wallet_saved_EUR[bot_id] + self.initial_wallet_saved_ETH[bot_id] * self.start_price)

		if order != {}:
			act = "{} {}".format(order["side"], order["type"])
			amt = "{:.4f}".format(order["amount"])
			p = "{:.4f}".format(order["price"])
		else:
			act = "IDLE"
			amt = ""
			p = ""

		col = tc.OKGREEN
		if percent_from_start < 0.0:
			col = tc.FAIL

		colg = tc.OKGREEN
		if gains < 0.0:
			colg = tc.FAIL

		suc = tc.WARNING

		# Display Bot Infos
		print(tc.HEADER + tc.BOLD + str(bot.name) + tc.ENDC)
		print("\rWallet : \t{:.5f} ETH  {:.2f} EUR ".format(wallet.getETH(), wallet.getEUR()) +\
				colg + "(savings {:.3f}%)".format(gains) +\
				tc.ENDC + " ({:.3f}% no inflation)".format(gains_no_inflation) + tc.ENDC)
		print("\rValue : \t{:.2f} EUR".format(value) + col + "  ({:.3f}%)".format(percent_from_start * 100) + tc.ENDC)
		print("\rPass/Cancel :\t{:1.0f} / {:1.0f}".format(self.order_passed[bot_id], self.order_cancelled[bot_id]))
		print("\rNew order : \t" + suc + "{} Price {} ETH Amt. {} ETH".format(act, p, amt) + tc.ENDC)
		print("\nWaiting orders")

		# Print last orders
		l = len(self.waiting_orders[bot_id])
		for i in range(min(10, l)):
			s = self.waiting_orders[bot_id][i]
			print("\r\t" + tc.OKBLUE + "{} {} {:.4f} ETH".format(s["side"], s["type"], s["price"]) + tc.ENDC)
		if(l > 10):
			print("\r\t" + tc.OKBLUE + "..." + tc.ENDC)
			print("\r")
		print("\r\n")

	def displayFinalBotsInfo(self):
		for b in self.bots:
			print(tc.HEADER + tc.BOLD + str(b.name) + tc.ENDC)
			b.displayResults()
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
		TradingBOT_Tendancy(Wallet(ETH_amount, EUR_amout), price),
		TradingBOT_Manual(Wallet(ETH_amount, EUR_amout), price)]

	# Launch simulation
	S = Simulator(B, typ)
	S.run()
