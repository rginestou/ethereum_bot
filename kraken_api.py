import krakenex
import time

k = krakenex.API()
k.load_key('kraken.key')

def getBalance():
	return k.query_private('Balance')

def getTime():
	r =  k.query_public('Time')
	return r['error'], r['result']

def getTickerInfo(pair='XETHZEUR'):
	r =  k.query_public('Ticker', {
		'pair': pair
	})
	error = r['error']
	if len(error) == 0:
		return r['result']
	else:
		return error

def addOrder(type, ordertype, price, volume, expiretm='0', pair='XETHZEUR'):
	r =  k.query_private('AddOrder', {
		'pair': pair,
		'type' : type,
		'ordertype' : ordertype,
		'price' : price,
		'volume' : volume,
		'expiretm' : expiretm
	})
	error = r['error']
	if len(error) == 0:
		return r['result']
	else:
		return error

if __name__ == '__main__':
	# print(getTickerInfo())
	print(addOrder('buy', 'market', 130, 0.001))
