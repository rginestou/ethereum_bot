from wallet import Wallet
import time
from math import log2, sqrt
import matplotlib.pyplot as plt

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100
MIN_PERIOD = 3

class TradingBOT_Tendancy:
	"""THE Tendancy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Tendancy"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()

		# Store price history
		self.price_history = []
		self.periods = [[]]
		self.histogram = [0]*8

	def orderBasedOnTendancy(self, m1, m2, current_price, best_ask, best_bid, p, expo):
		past_diff = m2 - m1
		curr_diff = current_price - m2

		# Models TODO
		o_side = "IDLE"
		if curr_diff > 0:
			if past_diff > 0:
				if curr_diff > past_diff:
					# Long increasing growth
					o_side = "SELL"
					o_price = best_ask + p * 0.01
					self.histogram[0] += 1
				else:
					# Long decreasing growth
					o_side = "SELL"
					o_price = best_ask + p * 0.001
					self.histogram[1] += 1
			else:
				if curr_diff > -past_diff:
					# Sharp through
					o_side = "SELL"
					o_price = best_ask + p * 0.01
					self.histogram[2] += 1
				else:
					# Feeble through
					o_side = "SELL"
					o_price = best_ask + p * 0.001
					self.histogram[3] += 1
		elif curr_diff < 0:
			if past_diff > 0:
				if -curr_diff > past_diff:
					# Sharp peak
					o_side = "BUY"
					o_price = best_bid - p * 0.001
					self.histogram[4] += 1
				else:
					# Small peak
					o_side = "BUY"
					o_price = best_bid - p * 0.01
					self.histogram[5] += 1
			else:
				if -curr_diff > -past_diff:
					# Falling cliff
					o_side = "BUY"
					o_price = best_bid - p * 0.02
					self.histogram[6] += 1
				else:
					# Falling through
					o_side = "BUY"
					o_price = best_bid - p * 0.02
					self.histogram[7] += 1

		# Runtime TODO
		o_runtime = expo * 60

		# Give more weight to the long orders TODO
		o_amount = expo * 0.0001

		if o_side != "IDLE":
			# Craft order
			return {
				"side" : o_side,
				"type" : "LIMIT",
				"runtime" : o_runtime,
				"price" : o_price,
				"amount" : o_amount
			}
		else:
			return {}

	def getOrders(self, asks, bids, current_price):
		# Format : {
		# 	"side" : SELL/BUY
		# 	"type" : MARKET, LIMIT
		# 	"runtime" : T
		# 	"price" : X
		# 	"amount" : Y
		# }

		# Update history
		self.price_history.append(current_price)
		N = len(self.price_history)

		# Has to have enough samples
		if N < 16:
			return {}

		# Ask/Bids
		best_ask = asks[0][0]
		best_bid = bids[0][0]

		# Establish the profile of the past periods
		p = 1
		len_p = len(self.periods)
		n = N
		expo2 = 2
		new_orders = []
		while n >=1:
			# Power of two ?
			if n % 2 == 0:
				# Only consider large periodes
				if p > MIN_PERIOD:
					# Add period if does not exist
					if len_p < p:
						self.periods.append([])
					self.periods[p-MIN_PERIOD].append(sum(self.price_history[N - expo2:])/expo2)

					# Query an order
					if len(self.periods[p-MIN_PERIOD]) >= 2:
						new_orders.append(self.orderBasedOnTendancy(self.periods[p-MIN_PERIOD][-2],
															self.periods[p-MIN_PERIOD][-1],
															current_price,
															best_ask,
															best_bid,
															p, expo2))
			else:
				break

			n = n // 2
			p += 1
			expo2 *= 2

		# Check if the orders are good
		for o in list(new_orders):
			if o == {}:
				new_orders.remove(o)
				continue

			# Is amount not enough?
			if o["amount"] < 0.00005:
				new_orders.remove(o)
				continue

			# Is compatible with account balance ?
			if o["side"] == "SELL":
				cost = o["amount"]
				if self.wallet.getETH() < self.wallet.getSavedETH() + cost:
					new_orders.remove(o)
					continue
			elif o["side"] == "BUY":
				cost = o["price"] * o["amount"]
				if self.wallet.getEUR() < self.wallet.getSavedEUR() + cost:
					new_orders.remove(o)
					continue

		return new_orders

	def getOrdersToCancel(self, waiting_orders):
		orders_to_cancel = []
		for o in waiting_orders:
			side = o['side']
			txid = o['txid']

			# Cancel orders to keep money
			if side == 'BUY' and self.wallet.getEUR() <= self.wallet.getSavedEUR()*1.2:
				orders_to_cancel.append(txid)
			if side == 'SELL' and self.wallet.getETH() <= self.wallet.getSavedETH()*1.2:
				orders_to_cancel.append(txid)

		return orders_to_cancel

	def displayResults(self):
		print(self.histogram)
		# plt.plot(self.periods[2])
		# plt.show()
