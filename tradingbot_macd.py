from wallet import Wallet
import time
import numpy as np
from math import log2, sqrt
from chartplot import chartPlot
import matplotlib.pyplot as plt

from order import Order
from tradingbot import TradingBot

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FEE = 0.16 / 100
P = 2

class TradingBot_MACD(TradingBot):
	"""THE Tendancy TradingBOT"""
	def __init__(self):
		# Initialize super class
		TradingBot.__init__(self, "MACD")

		# Initialize bot class
		self.periods = [5, 23, 138, 277]
		self.price_history_avg = dict.fromkeys(self.periods)
		self.MACD = dict.fromkeys(self.periods)
		self.signal = dict.fromkeys(self.periods)
		self.orders_history = dict.fromkeys(self.periods)
		self.previous_action = {"side":"IDLE", "price":1E99}

		# Plotting
		self.Xperiods = dict.fromkeys(self.periods)

		# Init dicts
		for p in self.periods:
			self.MACD[p] = np.array([])
			self.signal[p] = np.array([])
			self.price_history_avg[p] = np.array([])
			self.orders_history[p] = []
			self.Xperiods[p] = np.array([])


		self.stderr = ""

	def getNewOrders(self):
		"""
		Get new orders based on the current market state
		"""

		# Update averages
		self.computePriceAverage()
		market = self.market_evolution[-1]

		# Get order after computing signal
		orders = []
		for p in self.periods:
			if self.tick % p == 0:
				# Compute idicators at regular intervals
				self.Xperiods[p] = np.append(self.Xperiods[p], market.timestamp)
				self.computeMACD(p)
				self.computeSignal(p)

				# If enough data
				if self.tick > 2000 and p == self.periods[P]:
					if self.tick > p * (26+9+1):
						o = self.getOrderFromSignal(p, market.price)
						if o is not None:
							orders.append(o)
							self.stderr += str(o.price) + " " + str(o.side) + "\n"
							self.orders_history[p] = np.append(self.orders_history[p], o)

		# Increase ticker
		self.tick += 1

		return orders

	def getOrderFromSignal(self, period, current_price):
		market = self.market_evolution[-1]

		previous_sign = np.sign(self.MACD[period][-2] - self.signal[period][-2])
		current_sign = np.sign(self.MACD[period][-1] - self.signal[period][-1])

		# No action if still
		if previous_sign == current_sign:
			return None

		# Craft order magnitude
		amount = 0.00003 * period
		order = Order("", -1, amount, typ="LIMIT", runtime=period * 13 * 400)

		# Limit case
		should_verify = False
		if len(self.orders_history[period]) > 0:
			previous_order = self.orders_history[period][-1]
			should_verify = True
		# Determine order price and type
		if previous_sign < current_sign:
			# Increasing
			if not should_verify or (previous_order.side == "SELL" and previous_order.price > current_price):
				order.side = "BUY"
				order.price = market.best_bid - amount * FEE

				# Verification
				if self.wallet.EUR < order.price * amount:
					return None

				return order
		if previous_sign > current_sign:
			# Decreasing
			if not should_verify or (previous_order.side == "BUY" and previous_order.price < current_price):
				order.side = "SELL"
				order.price = market.best_ask + amount * FEE

				# Verification
				if self.wallet.ETH < amount:
					return None

				return order
		return None

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

	def movingAverage(self, x, N):
		weights = np.exp(np.linspace(-1., 0., N))
		weights /= weights.sum()

		avg = 0
		for i in range(1, N+1):
			avg += x[-i] * weights[N - i]
		return avg

	def computeMACD(self, period):
		if self.tick > period * 26:
			EMA12 = self.movingAverage(self.price_history_avg[period], 10)
			EMA26 = self.movingAverage(self.price_history_avg[period], 26)
			self.MACD[period] = np.append(self.MACD[period], EMA12 - EMA26)
		else:
			self.MACD[period] = np.append(self.MACD[period], 0)

	def computeSignal(self, period):
		if self.tick > period * (26+9):
			signal = self.movingAverage(self.MACD[period], 9)
		else:
			signal = 0
		self.signal[period] = np.append(self.signal[period], signal)

	def computePriceAverage(self):
		current_price = self.market_evolution[-1].price

		for p in self.periods:
			if self.tick % p == 0:
				# Compute the average
				if self.tick >= p:
					S = 0
					for i in range(p):
						S += self.market_evolution[-i].price
					new_avg = S/p
				else:
					new_avg = current_price
				self.price_history_avg[p] = np.append(self.price_history_avg[p], new_avg)

	def displayResults(self):
		# Print stderr
		print(self.stderr)

		period = self.periods[P]
		MACD = self.MACD[period]
		signal = self.signal[period]
		start_timestamp = self.market_evolution[0].timestamp

		X  = [s.timestamp - start_timestamp for s in self.market_evolution]
		Xp = self.Xperiods[period] - start_timestamp
		total_price_evolution = [s.price for s in self.market_evolution]
		total_savings_evolution = [100 * p.percent_increase_compared_to_not_sold for p in self.bot_performance]
		total_value_evolution = [p.wallet_value for p in self.bot_performance]
		# total_eth_evolution = [100 * p.ETH for p in self.bot_performance]

		plt.axhline(y=0.0, color='r', linestyle='-')
		for o, order in enumerate(self.passed_orders_history):
			pos = order.timestamp - start_timestamp
			if order.side == "SELL":
				plt.axvline(x=pos, color='red', linestyle='--')
				plt.text(pos, 20 * (o%2), "{:.2f}".format(order.price))
			if order.side == "BUY":
				plt.axvline(x=pos, color='green', linestyle='--')
				plt.text(pos, 20 * (o%2), "{:.2f}".format(order.price))
		plt.plot(X, total_price_evolution)
		plt.plot(X, total_savings_evolution)
		plt.plot(X, total_value_evolution)
		# plt.plot(X, total_eth_evolution)

		# MACD
		macd = 10*(MACD - signal)
		plt.fill_between(Xp, macd, 0, where=macd >= 0, facecolor='green', interpolate=True)
		plt.fill_between(Xp, macd, 0, where=macd <= 0, facecolor='red', interpolate=True)

		plt.draw()
		# chartPlot(self.price_history_avg[period], self.orders_history, period)
		return
