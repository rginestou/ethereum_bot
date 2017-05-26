from wallet import Wallet
import time

class TradingBOT_Dummy:
	"""THE Dummy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Dummy"
		self.wallet = wallet
		self.start_price = start_price
		self.start_time = time.time()

	def getAction(self, current_price):
		# Format : {
		# 	"order" : SELL/BUY
		# 	"amount" : X
		# }

		order = "IDLE"; amount = 0.0

		if current_price > self.start_price:
			order = "SELL"
			amount = 0.001

		if current_price < self.start_price:
			order = "BUY"
			amount = 0.001

		return { "order" : order, "amount" : amount }
