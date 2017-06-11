import matplotlib.pyplot as plt
import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from tradingbot import TradingBot, BotPerformance, MarketState
from wallet import Wallet
from order import Order
from utils import tc, signal_handler
import utils
from utils import STDERR

# Bots
from tradingbot_macd import TradingBot_MACD
from tradingbot_manual import TradingBot_Manual

LAPS = 2000

class Simulator:
	"""Simulates the stock context"""
	def __init__(self, bots, start_ETH, start_EUR, is_realtime=False, verbosity=False):
		self.bots = bots
		self.is_realtime = is_realtime
		self.verbosity = verbosity

		# Bot simulation
		self.market_evolution = []
		self.wallets = [Wallet(start_ETH, start_EUR, is_saving=True) for b in self.bots]
		self.bot_performances = [[] for b in self.bots]
		self.waiting_orders = [[] for b in self.bots]

		for bot_id, bot in enumerate(self.bots):
			bot.attachMarketEvolution(self.market_evolution)
			bot.attachWallet(self.wallets[bot_id])
			bot.attachBotPerformance(self.bot_performances[bot_id])

		# Stock simulation
		self.txid = 0
		self.order_cancelled = [0 for b in self.bots]
		self.order_passed = [0 for b in self.bots]
		self.final_price = -1

		# Instanciate API
		self.cryptowatch = CryptowatchAPI()

		self.stderr = ""

	def run(self):
		"""
		Run the actual simulation.
		Realtime or based on past samples.
		"""

		# Get initial value
		iter_n = 0

		len_history = 1E99
		if self.is_realtime:
			# Initiate from API
			start_price = self.cryptowatch.getCurrentPrice()
			iter_max = 1E99
		else:
			# Load file into memory
			with open("etheur_history_09_06_2017", "r") as f:
				history_samples = f.readlines()
				len_history = len(history_samples)
				history_samples = [MarketState(*list(map(float, x.strip().split('\t')))) for x in history_samples]
				start_price = history_samples[0].price
				iter_max = len_history

		# Main loop
		while utils.IS_RUNNING and iter_n < len_history:
			# Fetch info
			if self.is_realtime:
				# From the API
				orderbook = self.cryptowatch.getCurrentOrderbook()
				asks = orderbook["asks"]
				bids = orderbook["bids"]
				price = self.cryptowatch.getCurrentPrice()
				T = time.time()

				new_market_state = MarketState(T, price, asks[0], bids[0])

				iter_n += 1
				dt = self.cryptowatch.getTimeout()
			else:
				# From file
				new_market_state = history_samples[iter_n]
				T = new_market_state.timestamp

				iter_n += 1
				dt = 13

			# Update market evolution
			self.market_evolution.append(new_market_state)

			# Display simulator info
			if self.verbosity and (iter_n % LAPS == 0 or iter_n == len_history):
				self.displaySimulationInfo(iter_n, T, dt, iter_max)

			# Loop through all bots
			for bot_id, bot in enumerate(self.bots):
				# Request the bot action
				new_orders = bot.getNewOrders();

				if len(new_orders) > 0:
					pass
					# STDERR(self, str(len(new_orders)))

				# Compute transaction by adding the order to the stack
				self.computeTransaction(bot_id, new_orders)

				# Cancel orders ?
				self.cancelOrders(bot.getOrdersToCancel(self.waiting_orders[bot_id]), bot_id)

				# Update performances
				self.updateBotPerformance(bot_id)

				# Display bot info
				if self.verbosity and (iter_n % LAPS == 0 or iter_n == len_history):
					self.displayBotInfo(bot_id)

			# Wait for the next round if in real time mode
			if self.is_realtime:
				# Sleep a bit
				time.sleep(dt)

		# Stderr
		print(self.stderr)

		# Display final info
		self.displayFinalBotsInfo()


	def computeTransaction(self, bot_id, new_orders):
		market = self.market_evolution[-1]
		wallet = self.wallets[bot_id]

		for o in new_orders:
			if o is None:
				continue

			if o.amount < 0:
				continue

			o.timestamp = market.timestamp
			o.txid = self.txid
			self.txid += 1

			# Determine maker/taker for this order
			o.maker_taker = "maker"
			if (o.side == "SELL" and o.price < market.best_ask) or \
					(o.side == "BUY" and o.price > market.best_bid):
				o.maker_taker = "taker"

			self.waiting_orders[bot_id].append(o)

		# Loop throuh all waiting orders to update
		for o in list(self.waiting_orders[bot_id]):
			if market.timestamp - o.timestamp > o.runtime:
				# Cancel order
				self.waiting_orders[bot_id].remove(o)
				self.order_cancelled[bot_id] += 1
				continue

			success = False
			has_tried  = True
			if o.side == "SELL":
				if o.type == "LIMIT":
					if market.best_bid >= o.price:
						# Apply order
						# self.stderr += " sell) "+str(o.amount) +" "+ str(self.bots[bot_id].wallet.ETH) + "\n"
						success = wallet.convert(o.amount, o.price, "ETH_to_EUR", o.maker_taker)
					else:
						has_tried = False
				elif o.type == "MARKET":
					# Fetch the best bid immediately
					o.price = market.best_bid
					success = wallet.convert(o.amount, market.best_bid, "ETH_to_EUR", o.maker_taker)
			elif o.side == "BUY":
				if o.type == "LIMIT":
					if market.best_ask <= o.price:
						# Apply order
						# self.stderr += " buy) "+str(o.amount * o.price) +" "+ str(self.bots[bot_id].wallet.EUR) + "\n"
						success = wallet.convert(o.amount, o.price, "EUR_to_ETH", o.maker_taker)
					else:
						has_tried = False
				elif o.type == "MARKET":
					# Fetch the best ask immediately
					o.price = market.best_ask
					success = wallet.convert(o.amount, market.best_ask, "EUR_to_ETH", o.maker_taker)

			if success:
				# Appears in bot's history
				self.bots[bot_id].passed_orders_history.append(o)
				self.order_passed[bot_id] += 1
			elif has_tried:
				pass
				# self.stderr += "failure" + str(o.price)
			if has_tried:
				self.waiting_orders[bot_id].remove(o)

	def cancelOrders(self, cancel_txids, bot_id):
		for o in list(self.waiting_orders[bot_id]):
			if o.txid in cancel_txids:
				self.waiting_orders[bot_id].remove(o)
				self.order_cancelled[bot_id] += 1

	def getBotsFinalPerformance(self):
		# Return (savings %, value %)
		perf = []
		for b, bot in enumerate(self.bots):
			perf.append(self.updateBotPerformance(b))
		return perf

	def updateBotPerformance(self, bot_id):
		p = BotPerformance()
		start_price = self.market_evolution[0].price
		market = self.market_evolution[-1]
		wallet = self.wallets[bot_id]

		# ETH
		p.ETH = wallet.ETH

		# Savings
		p.savings = 100 * (wallet.saved - wallet.start_saved) / wallet.start_saved

		# Wallet value
		p.wallet_value = wallet.getValue(market.price)

		# Wallet value percent from start
		start_value = wallet.start_EUR + wallet.start_ETH * start_price
		p.percent_from_start = 100 * (p.wallet_value - start_value) / start_value

		# Wallet value no inflation
		p.wallet_value_no_inflation = wallet.EUR + wallet.ETH * start_price

		self.bot_performances[bot_id].append(p)

	def displaySimulationInfo(self, iter_n, T, dt, iter_max):
		# Common info
		start_price = self.market_evolution[0].price
		market = self.market_evolution[-1]
		inflation = 100 * ((market.price - start_price) / start_price)

		os.system('clear')
		print("\rBest bid\tPrice   \tBest ask" +\
				tc.ENDC + tc.BOLD + " ({:.3f} s/S)".format(dt) + tc.ENDC)
		print(tc.OKGREEN + "{:.4f}".format(market.best_bid) + tc.ENDC +\
				tc.HEADER + "\t{:.4f}".format(market.price) + tc.ENDC  +\
				tc.FAIL + "\t{:.4f}".format(market.best_ask) + tc.ENDC)
		print("\rInflation :\t{:.3f}%".format(inflation))
		hours = (T - self.market_evolution[0].timestamp) / 3600
		print("\rProgress :\t{:.2f}% ({:1.1f} h)".format(100 * iter_n / float(iter_max), hours))
		print("\n\r")

	def displayBotInfo(self, bot_id):
		perfs = self.bot_performances[bot_id][-1]
		wallet = self.wallets[bot_id]

		col = tc.OKGREEN
		if perfs.percent_from_start < 0.0:
			col = tc.FAIL

		colg = tc.OKGREEN
		if perfs.savings <= 0.0:
			colg = tc.FAIL

		# Display Bot Infos
		print(tc.HEADER + tc.BOLD + str(self.bots[bot_id].name) + tc.ENDC)
		print("\rWallet : \t{:.5f} ETH  {:.2f} EUR ".format(wallet.ETH, wallet.EUR) +\
				colg + "(savings {:.3f}%)".format(perfs.savings) + tc.ENDC)
		print("\rValue : \t{:.2f} EUR".format(perfs.wallet_value) + col + " ({:.3f}%)".format(perfs.percent_from_start) + tc.ENDC)
		print("\rPass/Cancel :\t{:1.0f} / {:1.0f}".format(self.order_passed[bot_id], self.order_cancelled[bot_id]))

		print("\r\n")

	def displayFinalBotsInfo(self):
		for b in self.bots:
			print(tc.HEADER + tc.BOLD + str(b.name) + tc.ENDC)
			plt.figure()
			b.displayResults()
		plt.show()


if __name__ == '__main__':
	# Bind Ctrl-C signal
	signal.signal(signal.SIGINT, signal_handler)

	# Request number of samples or time
	if len(sys.argv) < 4:
		print("Wrong input. Format is : samples/history ETH EUR")
		exit(0)

	is_realtime = sys.argv[1] == "sample"
	ETH_amount = float(sys.argv[2])
	EUR_amount = float(sys.argv[3])

	B = [TradingBot_MACD()] #, TradingBot_Manual()]

	# Launch simulation
	S = Simulator(B, ETH_amount, EUR_amount, is_realtime, verbosity=True)
	S.run()
	print(S.getBotsFinalPerformance())
