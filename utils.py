IS_RUNNING = True

def signal_handler(signal, frame):
	print('\r  ')
	global IS_RUNNING
	IS_RUNNING = False

class tc:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def STDERR(obj, message):
	obj.stderr += message + "\n"
