# ő lesz lefuttatva, amikor elindul

def setup():
	print('Do you want to create a new config? Y/N')
	create_new = input()
	if create_new.upper() == 'Y':
		createConfig()
	else:
		print('What existing config do you want to use?')
		config_name = input()
		try:
			config = json.loads(open('/config/' + config_name, 'r'))
		except:
			print("That config doesn't exist. Do you want to create it?")
			createConfig(*config_name)

def createConfig():
	print('Name of the new config:')
	input()
	

setup()