from wallet import Wallet

class TradingBOT:
	"""THE TradingBOT"""
	def __init__(self, wallet):
		self.wallet = wallet

	def getAction(self, current_price):
		# Format : {
		# 	"order" : SELL/BUY
		# 	"amount" : X
		# }

		if current_price > 140:
			order = "SELL"
			amount = 0.001

		if current_price < 140:
			order = "BUY"
			amount = 0.001

		return { "order" : order, "amount" : amount }
