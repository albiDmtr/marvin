import requests
import smtplib
import time
import traceback
import marvin_console
import os.path
import json

gmail_user = None
gmail_password = None
mail_to = None

with open(os.path.dirname(__file__) + '/mail_params.json', 'r') as json_file:
	mail_params = json.load(json_file)
	gmail_user = mail_params['bot_gmail_user']
	gmail_password = mail_params['bot_gmail_password']
	mail_to = mail_params['receiver_address']


def send_mail_to_me(subject, msg):
	# Create Email 
	mail_from = gmail_user
	mail_subject = subject
	mail_message_body = msg
	mail_message = '''\
From: %s
To: %s
Subject: %s
%s
''' % (mail_from, mail_to, mail_subject, mail_message_body)
	try:
		# Send Email
		server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
		server.login(gmail_user, gmail_password)
		server.sendmail(mail_from, mail_to, mail_message)
		server.close()
	except:
		marvin_console.error("Email failed to send.")

def exception(loop,context):
	marvin_console.error(str(context['exception']), custom_field={'traceback':traceback.print_tb(context['exception'].__traceback__),'task':context['future']})
	send_mail_to_me('Marvin crashed!',f"Error {str(context['exception'])}, Traceback {str(traceback.print_tb(context['exception'].__traceback__))}")
	loop.stop()
