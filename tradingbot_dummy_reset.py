from wallet import Wallet
import time

class TradingBOT_Dummy_Reset:
	"""THE Dummy TradingBOT"""
	def __init__(self, wallet, start_price):
		self.name = "Dummy Reset"
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

		# Reset time
		if time.time() - self.start_time > 100:
			self.start_time = time.time()

		return { "order" : order, "amount" : amount }
