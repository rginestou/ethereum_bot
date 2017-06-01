import time

class Order:
	def __init__(self, side, price, amount, typ="LIMIT", runtime=60):
		# Client specific
		self.side = side
		self.price = price
		self.amount = amount
		self.type = typ
		self.runtime = runtime

		# Transaction specific
		self.timestamp = -1
		self.txid = -1
		self.maker_taker = None
