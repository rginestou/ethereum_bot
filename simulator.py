import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from wallet import Wallet
from tradingbot import TradingBOT

IS_RUNNING = True

def signal_handler(signal, frame):
	print('\r  ')
	global IS_RUNNING
	IS_RUNNING = False

class Simulator:
	"""Simulates the stock context"""
	def __init__(self, bot, wallet, typ, val):
		self.bot = bot
		self.wallet = wallet
		self.simulation_type = typ
		self.simulation_value = val

		# Instanciate API
		self.cryptowatch = CryptowatchAPI()

	# Run simulation
	def run(self):
		startTime = time.time()
		T = startTime
		S = 0
		while IS_RUNNING and ((typ == 'time' and T - startTime < val) or (typ == 'samples' and S < val)):
			# Write info
			price = self.cryptowatch.getCurrentPrice()

			# Request the bot action
			action = self.bot.getAction(price);
			if action["order"] == "SELL":
				self.wallet.convert(action["amount"], price, "ETH_to_EUR")
			elif action["order"] == "BUY":
				self.wallet.convert(action["amount"], price, "EUR_to_ETH")

			# Increment
			T = time.time()
			S += 1
			dt = self.cryptowatch.getTimeout()

			# Display
			value = self.wallet.getEUR() + self.wallet.getETH() * price
			os.system('clear')
			print("\rPrice : \t{:.4f} ({:.3f} S/s)".format(price, 1.0 / dt))
			print("\rWallet : \t{:.5f} ETH  {:.2f} EUR".format(self.wallet.getETH(), self.wallet.getEUR()))
			print("\r\t\tValue : {:.2f} EUR".format(value))
			print("\n\rAction taken : {} of {:.4f}".format(action["order"], action["amount"]))
			print("\n\rTotal time : \t{:1.0f} s".format(T - startTime))

			# Sleep a bit
			time.sleep(dt)

if __name__ == '__main__':
	# Bind Ctrl-C signal
	signal.signal(signal.SIGINT, signal_handler)

	# Request number of samples or time
	if len(sys.argv) < 5:
		print("Wrong input. Format is : time/samples value(seconds/samples) ETH EUR")
		exit(0)

	typ = sys.argv[1]
	val = int(sys.argv[2])
	ETH_amount = float(sys.argv[3])
	EUR_amout = float(sys.argv[4])

	# Forever
	if val < 0:
		val = 1E99

	# New wallet
	W = Wallet(ETH_amount, EUR_amout)

	# Choose bot
	B = TradingBOT(W)

	# Launch simulation
	S = Simulator(B, W, typ, val)
	S.run()
