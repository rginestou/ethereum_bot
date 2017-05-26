from wallet import Wallet

class TradingBOT:
	"""THE TradingBOT"""
	def __init__(self, wallet, start_price):
		self.wallet = wallet
		self.start_price = start_price

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
