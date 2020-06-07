from credentials import email,password,to_email
from subprocess import run
import os
import re
import time
import yagmail
output = run(["uptime","-p"], capture_output=True).stdout.decode('unicode_escape').strip('\n')
uptime = int(re.findall(r'\d+', output)[0])
temperature = os.popen("vcgencmd measure_temp").readline().replace("temp=","")
current_time = time.strftime("%m/%d/%Y, %H:%M:%S")
body = f"""Hey Sachin!
Here's your daily Raspberry Pi update.
Time: {current_time}
Uptime: {uptime // 60} hours {uptime % 60} minutes
Temperature: {temperature}
The Stock Bot log file is attached.
~ Raspberry Pi :)"""
mail = yagmail.SMTP(email,password)
mail.send(to_email,'Raspberry Pi Daily Update',body,'StockBot/stockbot.log')