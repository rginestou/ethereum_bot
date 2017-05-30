from wallet import Wallet
import time
from math import log2, sqrt
from chartplot import chartPlot

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100
MIN_PERIOD = 7

class TradingBOT_Tendancy:
	"""THE Tendancy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Tendancy"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()
		self.order_id = 0

		# Store price history
		self.price_history = []
		self.periods = [[]]
		self.orders_history = []
		self.histogram = [[] for _ in range(8)]

	def orderBasedOnTendancy(self, m1, m2, m3, current_price, best_ask, best_bid, p, expo):
		past_diff = m2 - m1
		curr_diff = m3 - m2

		# Models TODO
		o_side = "IDLE"
		if curr_diff > 0:
			if past_diff > 0:
				if curr_diff > past_diff:
					# Long increasing growth
					o_side = "SELL"
					o_price = best_ask + p * 0.1
					# self.histogram[0] += 1
					o_side = "IDLE"
				else:
					# Long decreasing growth
					o_side = "SELL"
					o_price = best_ask + p * 0.11;
					# self.histogram[1] += 1
					o_side = "IDLE"
			else:
				if curr_diff > -past_diff:
					# Sharp through
					o_side = "SELL"
					o_price = best_ask + p * 0.01;
					# self.histogram[2] += 1
					o_side = "IDLE"
				else:
					# Feeble through
					o_side = "SELL"
					o_price = best_ask + p * 0.001;
					# self.histogram[3] += 1
					o_side = "IDLE"
		elif curr_diff < 0:
			if past_diff > 0:
				if -curr_diff > past_diff:
					# Sharp peak
					o_side = "BUY"
					o_price = best_bid - p * 0.001;
					# self.histogram[4] += 1
					o_side = "IDLE"
				else:
					# Small peak
					o_side = "SELL"
					o_price = best_ask + p * 0.001;
					self.histogram[5].append("{:.2f},{:.2f},{:.2f}".format(past_diff, curr_diff, current_price))
					# o_side = "IDLE"
			else:
				if -curr_diff > -past_diff:
					# Falling cliff
					o_side = "BUY"
					o_price = best_bid - p * 0.001;
					self.histogram[6].append("{:.2f},{:.2f},{:.2f}".format(past_diff, curr_diff, current_price))
					# o_side = "IDLE"
				else:
					# Falling through
					o_side = "BUY"
					o_price = best_bid - p * 0.1
					# self.histogram[7] += 1
					o_side = "IDLE"

		# Runtime TODO
		o_runtime = expo * 60
		o_runtime = 40 * 60

		# Give more weight to the long orders TODO
		o_amount = expo * 0.0004
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
		p = 0
		len_p = len(self.periods)
		n = N
		expo2 = 1
		new_orders = []
		while n >=1:
			# Power of two ?
			if n % 2 != 0:
				break

			# Only consider large periods
			if p < MIN_PERIOD:
				n = n // 2
				p += 1
				expo2 *= 2
				continue

			# Add period if does not exist
			if len_p <= p-MIN_PERIOD:
				self.periods.append([])
			self.periods[p-MIN_PERIOD].append(sum(self.price_history[N - expo2:])/expo2)

			# Query an order
			if len(self.periods[p-MIN_PERIOD]) >= 3:
				if p == MIN_PERIOD:
					new_order = self.orderBasedOnTendancy(self.periods[p-MIN_PERIOD][-3],
														self.periods[p-MIN_PERIOD][-2],
														self.periods[p-MIN_PERIOD][-1],
														current_price,
														best_ask,
														best_bid,
														p, expo2)
					# Check if the order is good
					if new_order != {}:
						# Is compatible with account balance ?
						is_good = True
						if new_order["side"] == "SELL":
							cost = new_order["amount"]
							if self.wallet.getETH() < self.wallet.getSavedETH() + cost:
								is_good = False
						elif new_order["side"] == "BUY":
							cost = new_order["price"] * new_order["amount"]
							if self.wallet.getEUR() < self.wallet.getSavedEUR() + cost:
								is_good = False

						if is_good:
							new_order["id"] = self.order_id; self.order_id += 1
							new_orders.append(new_order)
							self.orders_history[-1].append(new_order)
							self.orders_history[-1]["period"] = p-MIN_PERIOD
					else:
						self.orders_history[-1].append({"period":p-MIN_PERIOD, "side": "IDLE", "id":-1})
			else:
				self.orders_history[-1].append({"period":p-MIN_PERIOD, "side": "IDLE", "id":-1})

			n = n // 2
			p += 1
			expo2 *= 2

		return new_orders

	def getOrdersToCancel(self, waiting_orders):
		orders_to_cancel = []
		for o in waiting_orders:
			side = o['side']
			txid = o['txid']

			# Cancel orders to keep money
			if side == 'BUY' and self.wallet.getEUR() <= self.wallet.getSavedEUR()*1.2:
				orders_to_cancel.append(txid)
				for h in self.orders_history:
					pass
			if side == 'SELL' and self.wallet.getETH() <= self.wallet.getSavedETH()*1.2:
				orders_to_cancel.append(txid)

		return orders_to_cancel

	def displayResults(self):
		print(sum([len(x) for x in self.histogram]))
		chartPlot(self.periods[0], self.orders_history[0])
		return
