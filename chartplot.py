import matplotlib.pyplot as plt

def chartPlot(periods, orders, p=1):
	plt.plot(periods)
	ordo = min(periods)
	for o, order in enumerate(orders):
		if order["side"] == "SELL":
			plt.axvline(x=o*p, color='red', linestyle='--')
			plt.text(o, ordo + 2 * (o%2), "{:.2f}".format(order["price"]))
		if order["side"] == "BUY":
			plt.axvline(x=o*p, color='green', linestyle='--')
			plt.text(o, ordo + 2 * (o%2), "{:.2f}".format(order["price"]))
	plt.show()
