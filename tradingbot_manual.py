import matplotlib.pyplot as plt
import time

from tradingbot import TradingBot
from order import Order
from wallet import Wallet

NET_PERCENTAGE_UP = 1 + 0.16 / 100
NET_PERCENTAGE_DOWN = 1 - 0.16 / 100
FRACTION = 0.16 / 100

class TradingBot_Manual(TradingBot):
	"""THE Manual TradingBOT"""
	def __init__(self):
		# Initialize super class
		TradingBot.__init__(self, "Manual")

	def getNewOrders(self):
		market = self.market_evolution[-1]
		orders = []

		amount = 0.05
		# if self.tick == 6000:
		# 	orders.append(Order("SELL", -1, amount, typ="MARKET", runtime=40*60))
		if self.tick == 8000:
			orders.append(Order("BUY", -1, amount, typ="MARKET", runtime=40*60))
		if self.tick == 10000:
			orders.append(Order("SELL", -1, amount, typ="MARKET", runtime=40*60))
		if self.tick == 15000:
			orders.append(Order("BUY", -1, amount, typ="MARKET", runtime=40*60))
		if self.tick == 20000:
			orders.append(Order("SELL", -1, amount, typ="MARKET", runtime=40*60))

		self.tick += 1

		return orders

	def getOrdersToCancel(self, waiting_orders):
		orders_to_cancel = []
		for o in waiting_orders:
			side = o['side']
			txid = o['txid']

			# Cancel orders to keep money
			if side == 'BUY' and self.wallet.getEUR() <= self.wallet.getSavedEUR()*1.2:
				orders_to_cancel.append(txid)
			if side == 'SELL' and self.wallet.getETH() <= self.wallet.getSavedETH()*1.2:
				orders_to_cancel.append(txid)

		return orders_to_cancel

	def displayResults(self):
		start_timestamp = self.market_evolution[0].timestamp

		X  = [s.timestamp - start_timestamp for s in self.market_evolution]
		total_price_evolution = [s.price for s in self.market_evolution]
		total_savings_evolution = [500 * p.savings for p in self.bot_performance]
		total_value_evolution = [p.wallet_value for p in self.bot_performance]

		plt.axhline(y=0.0, color='r', linestyle='-')
		for o, order in enumerate(self.passed_orders_history):
			pos = order.timestamp - start_timestamp
			if order.side == "SELL":
				plt.axvline(x=pos, color='red', linestyle='--')
				plt.text(pos, 20 * (o%2), "{:.2f}".format(order.price))
			if order.side == "BUY":
				plt.axvline(x=pos, color='green', linestyle='--')
				plt.text(pos, 20 * (o%2), "{:.2f}".format(order.price))
		plt.plot(X, total_price_evolution)
		plt.plot(X, total_savings_evolution)
		plt.plot(X, total_value_evolution)

		plt.draw()
