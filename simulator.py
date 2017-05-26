import os, sys
import time
import signal

from cryptowatchapi import CryptowatchAPI
from wallet import Wallet
from tradingbot_dummy import TradingBOT_Dummy
from tradingbot_dummy_reset import TradingBOT_Dummy_Reset
from utils import bcolors, signal_handler
import utils

class Simulator:
	"""Simulates the stock context"""
	def __init__(self, bots, typ, val):
		self.bots = bots
		self.simulation_type = typ
		self.simulation_value = val

		# Instanciate API
		self.cryptowatch = CryptowatchAPI()

	# Run simulation
	def run(self):
		# Get initial value
		price = self.cryptowatch.getCurrentPrice()
		initial_values = [bot.wallet.getEUR() + bot.wallet.getETH() * price for bot in self.bots]

		# Run
		startTime = time.time()
		T = startTime
		S = 0
		while utils.IS_RUNNING and ((typ == 'time' and T - startTime < val) or (typ == 'samples' and S < val)):
			# Write info
			price = self.cryptowatch.getCurrentPrice()
			if price < 0:
				# Something went wrong, cool down
				time.sleep(5.0)

			# Increment
			T = time.time()
			S += 1
			dt = self.cryptowatch.getTimeout()

			# Common info
			os.system('clear')
			print("\rPrice : \t" + bcolors.HEADER + "{:.4f}".format(price) + \
			bcolors.ENDC + bcolors.BOLD + " ({:.3f} S/s)".format(1.0 / dt) + bcolors.ENDC)
			print("\rTotal time : \t{:1.0f} s".format(T - startTime))
			print("\n\n")

			# Loop through all bots
			for b, bot in enumerate(self.bots):
				# Request the bot action
				action = bot.getAction(price);
				wallet = bot.wallet

				succeeded = True
				if action["order"] == "SELL":
					succeeded = wallet.convert(action["amount"], price, "ETH_to_EUR")
				elif action["order"] == "BUY":
					succeeded = wallet.convert(action["amount"], price, "EUR_to_ETH")

				# Display
				value = wallet.getEUR() + wallet.getETH() * price
				percent_from_start = (value - initial_values[b]) / initial_values[b]
				col = bcolors.OKGREEN
				act = action["order"]
				amt = "{:.4f}".format(action["amount"])
				suc = bcolors.OKBLUE
				if act == "IDLE":
					amount = ""
				if percent_from_start < 0.0:
					col = bcolors.FAIL
				if not succeeded:
					suc = bcolors.WARNING

				# Display Bot Infos
				print(bcolors.HEADER + bcolors.BOLD + str(bot.name) + bcolors.ENDC)
				print("\rWallet : \t{:.5f} ETH  {:.2f} EUR".format(wallet.getETH(), wallet.getEUR()))
				print("\rValue : \t{:.2f} EUR".format(value) + col + "  ({:.3f}%)".format(percent_from_start * 100) + bcolors.ENDC)
				print("\n\rAction taken : " + suc + "{} of {}".format(act, amt) + bcolors.ENDC)
				print("\n")
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

	# Init bots
	price = CryptowatchAPI().getCurrentPrice()
	B = [TradingBOT_Dummy(Wallet(ETH_amount, EUR_amout), price),
		TradingBOT_Dummy_Reset(Wallet(ETH_amount, EUR_amout), price)]

	# Launch simulation
	S = Simulator(B, typ, val)
	S.run()
