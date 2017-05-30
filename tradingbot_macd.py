from wallet import Wallet
import time
from math import log2, sqrt
from chartplot import chartPlot
import matplotlib.pyplot as plt

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100
MIN_PERIOD = 7

class TradingBOT_MACD:
	"""THE Tendancy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "MACD"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()
		self.tick = 0

		# Store price history
		self.price_history = []
		self.periods = [5, 10, 60, 277]
		self.price_history_avg = dict.fromkeys(self.periods)
		self.MACD = dict.fromkeys(self.periods)
		self.signal = dict.fromkeys(self.periods)

		# Init dicts
		for p in self.periods:
			self.MACD[p] = []
			self.signal[p] = []
			self.price_history_avg[p] = []

	def getOrders(self, asks, bids, current_price):
		# Format : {
		# 	"side" : SELL/BUY
		# 	"type" : MARKET, LIMIT
		# 	"runtime" : T
		# 	"price" : X
		# 	"amount" : Y
		# }

		# Update history
		self.computePriceAverage(current_price)

		# Ask/Bids
		best_ask = asks[0][0]
		best_bid = bids[0][0]

		# Compute signal
		for p in self.periods:
			self.computeSignal(9, p)

			# Not enough data yet ?


		self.tick += 1

		return {}

	def getOrdersToCancel(self, waiting_orders):
		orders_to_cancel = []
		# for o in waiting_orders:
		# 	side = o['side']
		# 	txid = o['txid']
		#
		# 	# Cancel orders to keep money
		# 	if side == 'BUY' and self.wallet.getEUR() <= self.wallet.getSavedEUR()*1.2:
		# 		orders_to_cancel.append(txid)
		# 		for h in self.orders_history:
		# 			pass
		# 	if side == 'SELL' and self.wallet.getETH() <= self.wallet.getSavedETH()*1.2:
		# 		orders_to_cancel.append(txid)

		return orders_to_cancel

	def computeEMA(self, N, period):
		K = 2 / (N + 1)
		if self.tick >= period * N:
			ema = self.price_history_avg[period][-N]
		else:
			ema = self.price_history[-1]
		for k in range(1, N):
			if self.tick >= period * (N - k):
				ema = self.price_history_avg[period][-N+k] * K + (1 - K) * ema
			else:
				ema = self.price_history[-1]
		return ema

	def computeSignal(self, N, period):
		if self.tick % period == 0:
			# Compute MACD
			EMA12 = self.computeEMA(12, period)
			EMA26 = self.computeEMA(26, period)
			self.MACD[period].append(EMA12 - EMA26)

			# Compute signal
			K = 2 / (N + 1)
			if self.tick >= period * N:
				signal = self.MACD[period][-N]
			else:
				signal = 0
			for k in range(1, N):
				if self.tick >= period * (N - k):
					signal = self.MACD[period][-N + k] * K + (1 - K) * signal
				else:
					signal = 0
			self.signal[period].append(signal)

	def computePriceAverage(self, new_price):
		self.price_history.append(new_price)

		for p in self.periods:
			if self.tick % p == 0:
				# Compute the average
				if self.tick >= p:
					self.price_history_avg[p].append(sum(self.price_history[-p:])/p)
				else:
					self.price_history_avg[p].append(self.price_history[-1])
	def displayResults(self):
		plt.plot([5*s for s in self.signal[self.periods[3]]])
		plt.plot([s-100 for s in self.price_history_avg[self.periods[-1]]])
		# l = len(self.signal[self.periods[3]]); p = self.periods[3]
		# X = [x for x in range(0, p*l, p)]
		# plt.plot(X, [5*s for s in self.signal[self.periods[3]]])
		# plt.plot([s-100 for s in self.price_history])
		plt.show()
		# chartPlot(self.signal[self.periods[3]], [])
		return
