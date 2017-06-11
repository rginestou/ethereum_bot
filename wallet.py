net_percentage = {"maker" : 1 - 0.16 / 100,
				"taker" : 1 - 0.26 / 100}

class Wallet:
	"""Basic Wallet"""
	def __init__(self, ETH, EUR, is_saving=False):
		self.ETH = ETH
		self.EUR = EUR
		self.start_ETH = ETH
		self.start_EUR = EUR
		self.saved = EUR / 2
		self.start_saved = EUR / 2

		self.is_saving = is_saving

	# Assumed that the amount is given in ETH
	def convert(self, amount, price, direction, maker_taker):
		net_amount = amount * net_percentage[maker_taker]

		if direction == "ETH_to_EUR":
			if (self.ETH < amount):
				return False
			self.ETH -= amount
			self.EUR += net_amount * price
			
			# Refresh savings according to growth
			if self.is_saving and self.saved < self.EUR / 2:
				self.saved = self.EUR / 2
		elif direction == "EUR_to_ETH":
			if (self.EUR < amount * price):
				return False
			self.ETH += net_amount
			self.EUR -= amount * price

		return True

	def getValue(self, price):
		return self.EUR + self.ETH * price
