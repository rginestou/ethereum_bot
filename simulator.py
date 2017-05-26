import os, sys
import time

from . import CryptowatchAPI, Wallet
from . import TradingBOT

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
		while (typ == 'time' and T - startTime < val) or (typ == 'samples' and S < val):
			# Write info
			price = cryptowatch.getCurrentPrice()
			f.write("{:.4f}\n".format(price))

			# Increment
			T = time.time()
			S += 1
			os.system('clear')
			sys.stdout.write("\rCurrent price : {:.4f} ({:.3f} S/s)".format(price,1.0 / dt))
			sys.stdout.flush()

			# Sleep a bit
			dt = cryptowatch.getTimeout()
			time.sleep(dt)

		sys.stdout.write("\n")

if __name__ == '__main__':
	# Request number of samples or time
	if len(sys.argv) < 5:
		print("Wrong input. Format is : time/samples value(seconds/samples) ETH EUR")
		exit(0)

	typ = sys.argv[1]
	val = int(sys.argv[2])
	ETH_amount = sys.argv[3]
	EUR_amout = int(sys.argv[4])

	# New wallet
	W = Wallet(ETH_amount, EUR_amout)

	# Choose bot
	B = TradingBOT()

	# Launch simulation
	S = Simulator(B, W, typ, val)
	S.run()
