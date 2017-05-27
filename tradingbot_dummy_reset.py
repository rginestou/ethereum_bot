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

	def getOrder(self, asks, bids, current_price):
		# Format : {
		# 	"side" : SELL/BUY
		# 	"type" : MARKET, LIMIT
		# 	"runtime" : T
		# 	"price" : X
		# 	"amount" : Y
		# }

		order = {}

		if current_price > self.start_price:
			# Compute
			amount_to_sell = 0.0010
			price_to_sell = self.start_price + amount_to_sell * FRACTION

			if current_price > price_to_sell:
				# Craft order
				order = {
					"side" : "SELL",
					"type" : "LIMIT",
					"runtime" : 120,
					"price" : price_to_sell,
					"amount" : amount_to_sell
				}

		if current_price < self.start_price:
			# Compute
			amount_to_buy = 0.0010
			price_to_buy = self.start_price - amount_to_buy * FRACTION

			if current_price < price_to_buy:
				# Craft order
				order = {
					"side" : "BUY",
					"type" : "LIMIT",
					"runtime" : 120,
					"price" : price_to_buy,
					"amount" : amount_to_buy
				}

		# Reset time
		if time.time() - self.start_time > 60:
			self.start_time = time.time()
			self.start_price = current_price

		return order
