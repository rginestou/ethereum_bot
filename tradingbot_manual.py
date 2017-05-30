from wallet import Wallet
import time

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100

class TradingBOT_Manual:
	"""THE Dummy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Manual"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()
		self.previous_orders = []

	def getOrders(self, asks, bids, current_price):
		# Format : {
		# 	"side" : SELL/BUY
		# 	"type" : MARKET, LIMIT
		# 	"runtime" : T
		# 	"price" : X
		# 	"amount" : Y
		# }

		order = {}

		if current_price > 133 and len(self.previous_orders) == 0:
			price_to_buy = 132
			amount_to_buy = 0.15

			# Craft order
			order = {
			"side" : "BUY",
			"type" : "MARKET",
			"runtime" : 40*60,
			"price" : price_to_buy,
			"amount" : amount_to_buy
			}

			self.previous_orders.append(order)

		if current_price > 155 and len(self.previous_orders) == 1:
			price_to_sell = 156
			amount_to_sell = 0.15

			# Craft order
			order = {
			"side" : "SELL",
			"type" : "LIMIT",
			"runtime" : 40*60,
			"price" : price_to_sell,
			"amount" : amount_to_sell
			}

			self.previous_orders.append(order)

		return [order]

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
		pass
