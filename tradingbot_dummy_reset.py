from wallet import Wallet
import time

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100

class TradingBOT_Dummy_Reset:
	"""THE Dummy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Dummy Reset"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()

	def getOrders(self, asks, bids, current_price):
		# Format : {
		# 	"side" : SELL/BUY
		# 	"type" : MARKET, LIMIT
		# 	"runtime" : T
		# 	"price" : X
		# 	"amount" : Y
		# }

		order = {}

		# Ask/Bids
		best_ask = asks[0][0]
		best_bid = bids[0][0]

		if current_price > self.start_price:
			amount_to_sell = 0.0010
			# Keep some ether
			if self.wallet.getETH() > self.wallet.getSavedETH() + amount_to_sell:
				price_to_sell = best_ask + 0.05

				# Craft order
				order = {
					"side" : "SELL",
					"type" : "LIMIT",
					"runtime" : 5*60,
					"price" : price_to_sell,
					"amount" : amount_to_sell
				}

		if current_price < self.start_price:
			amount_to_buy = 0.0010
			# Keep some euros
			if self.wallet.getEUR() > self.wallet.getSavedEUR() + amount_to_buy * current_price:
				price_to_buy = best_bid - 0.05

				# Craft order
				order = {
					"side" : "BUY",
					"type" : "LIMIT",
					"runtime" : 5*60,
					"price" : price_to_buy,
					"amount" : amount_to_buy
				}

		# Reset time
		if time.time() - self.start_time > 200:
			self.start_time = time.time()
			self.start_price = current_price

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
