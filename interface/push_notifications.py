import requests
import smtplib
import time
import traceback
import marvin_console

def send_mail_to_me(subject, msg):
	# Set Global Variables
	gmail_user = 'noreply.marvincrypto@gmail.com'
	gmail_password = '***REMOVED***'
	# Create Email 
	mail_from = gmail_user
	mail_to = 'domotor.albert@gmail.com'
	mail_subject = subject
	mail_message_body = msg
	mail_message = '''\
From: %s
To: %s
Subject: %s
%s
''' % (mail_from, mail_to, mail_subject, mail_message_body)
	# Sent Email
	server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
	server.login(gmail_user, gmail_password)
	server.sendmail(mail_from, mail_to, mail_message)
	server.close()

def exception(loop,context):
	marvin_console.error(str(context['exception']), custom_field={'traceback':traceback.print_tb(context['exception'].__traceback__),'task':context['future']})
	send_mail_to_me('Marvin crashed!',f"Error {str(context['exception'])}, Traceback {str(traceback.print_tb(context['exception'].__traceback__))}")
	loop.stop()