class TradingBot:
	"""Template for TradingBot"""
	def __init__(self, name):
		# Passed attributes
		self.name = name

		# To be attached
		self.market_evolution = None
		self.wallet = None
		self.bot_performance = None

		self.tick = 0
		self.passed_orders_history = []

	def getNewOrders(self):
		pass

	def getOrdersToCancel(self):
		pass

	def displayResults(self):
		pass

	def attachMarketEvolution(self, market_evolution):
		self.market_evolution = market_evolution

	def attachWallet(self, wallet):
		self.wallet = wallet

	def attachBotPerformance(self, bot_performance):
		self.bot_performance = bot_performance

	def displayHistory(self):
		pass

class BotPerformance:
	def __init__(self):
		self.ETH = 0
		self.savings = 0
		self.wallet_value = 0
		self.percent_from_start = 0
		self.wallet_value_no_inflation = 0
		self.wallet_value_if_half_sold = 0
		self.percent_increase_compared_to_half_sold = 0

class MarketState:
	def __init__(self, timestamp, price, best_ask, best_bid):
		self.timestamp = timestamp
		self.price = price
		self.best_ask = best_ask
		self.best_bid = best_bid
