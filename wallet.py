class Wallet:
	"""Basic Wallet"""
	def __init__(self, ETH, EUR):
		self.ETH = ETH
		self.EUR = EUR

	# Assumed that the amount is given in ETH
	def convert(self, amount, price, direction):
		if direction == "ETH_to_EUR":
			self.ETH -= amount
			self.EUR += amount * price
		elif direction == "EUR_to_ETH":
			self.EUR -= amount * price
			self.ETH += amount

	def getETH(self):
		return self.ETH

	def getEUR(self):
		return self.EUR
