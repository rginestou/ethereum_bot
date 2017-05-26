class Wallet:
	"""Basic Wallet"""
	def __init__(self, ETH, EUR):
		self.ETH = ETH
		self.EUR = EUR

	# Assumed that the amount is given in ETH
	def convert(self, amount, price, direction):
		success = False
		if direction == "ETH_to_EUR":
			if (self.ETH >= amount):
				success = True
			self.ETH -= amount
			self.EUR += amount * price

		elif direction == "EUR_to_ETH":
			if (self.EUR >= amount * price):
				success = True
			self.EUR -= amount * price
			self.ETH += amount

		return success

	def getETH(self):
		return self.ETH

	def getEUR(self):
		return self.EUR
