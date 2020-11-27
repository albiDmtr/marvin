import requests

def exception(loop,context):
	 msg = context.get("exception", context["message"])