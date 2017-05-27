import json
import requests
import urllib.request
import urllib.parse
import urllib.error
import time
import utils
import os, sys

class CryptowatchAPI:
	"""Fetch data from Cryptowat.ch"""
	def __init__(self):
		# API specifications
		self.uri = "https://api.cryptowat.ch/markets/kraken/etheur"
		self.total_allowance = 4.0
		self.averaged_cost = 0.0
		self.cumulated_cost = 0.0
		self.iterations = 0

	def _makeRequest(self, url):
		response = {}
		while utils.IS_RUNNING:
			try:
				r = requests.get(self.uri + url)
				response = json.loads(r.text)
			except:
				pass

			if 'result' in response:
				break

			if 'error' in response:
				print(response['error'])

			time.sleep(5)

		# Parse result
		try:
			cost = response['allowance']['cost'] * 1E-9

			# Update allowance
			self.iterations += 1
			self.cumulated_cost += cost
			self.averaged_cost = self.cumulated_cost / self.iterations

			return response['result']
		except:
			self.averaged_cost += 5.0
			return { "price" : -1 }

	def getCurrentPrice(self):
		res = self._makeRequest("/price")
		return float(res['price'])

	def getCurrentOrderbook(self):
		return self._makeRequest("/orderbook")

	def getTimeout(self):
		return max(12, 1.5 * (self.total_allowance / 3600.0 / self.averaged_cost))

	def close(self):
		pass

if __name__ == '__main__':
	# Connection
	cryptowatch = CryptowatchAPI()

	# Request number of samples or time
	if len(sys.argv) < 3:
		print("Wrong input. Format is : time/samples value(seconds/samples)")
		exit(0)

	typ = sys.argv[1]
	val = int(sys.argv[2])

	with open('etheur_chart.txt', 'w') as f:
		startTime = time.time()
		T = startTime
		S = 0
		while (typ == 'time' and T - startTime < val) or (typ == 'samples' and S < val):
			# Write info
			price = cryptowatch.getCurrentPrice()
			f.write("{:.4f}\n".format(price))

			# Sleep a bit
			dt = cryptowatch.getTimeout()
			time.sleep(dt)

			# Increment
			T = time.time()
			S += 1
			# os.system('clear')
			sys.stdout.write("\rCurrent price : {:.4f} ({:.3f} S/s)".format(price,1.0 / dt))
			sys.stdout.flush()

	sys.stdout.write("\n")

	# Done
	cryptowatch.close()
