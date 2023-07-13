# This little program is for the Waveshare 7.5
# inch Version 2 black and white only epaper display
# It uses OpenWeatherMap API to display weather info
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')

# Search lib folder for display driver modules
sys.path.append('lib')
from waveshare_epd import epd7in5_V2
epd = epd7in5_V2.EPD()

from datetime import datetime
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
import requests, json
from io import BytesIO
import csv
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from datetime import timezone
from dateutil import tz

# function to load secrets
def secretFunc():
	load_dotenv()
	global TRANSIT_URL
	global TRANSIT_API_KEY
	global STOPCODES
	global DIRECTIONS
	global OPERATORS
	global STOPNAMES
	global OPENWEATHER_API_KEY

	TRANSIT_URL = 'http://api.511.org/transit/StopMonitoring/'
	TRANSIT_API_KEY = os.environ['TRANSIT_API_KEY']
	OPENWEATHER_API_KEY = os.environ['OPENWEATHER_API_KEY']

	# update STOPCODES, OPERATORS, DIRECTIONS, STOPNAMES to add add'l stops

	STOPCODES = [13915, 13914, 14509, 14510]

	OPERATORS = ['SF','SF', 'SF', 'SF']

	DIRECTIONS = ['Inbound', 'Outbound', 'Inbound', 'Outbound']

	STOPNAMES = ['Stanyan', 'Stanyan', 'Folsom', 'Folsom']

	return()

# function to use 511org API to find next arrivals at each of the provided STOPCODES
def getNextTransit():
	secretFunc()
	arrivals = list()
	for i, stop in enumerate(STOPCODES):
		r = requests.get(TRANSIT_URL, 
						 params = {'agency': OPERATORS[i], 
								   'api_key': TRANSIT_API_KEY,
								   'stopcode': stop})
		
		content = json.loads(r.content)

		stopInfo = pd.DataFrame.from_records(content)
		stopInfo = stopInfo['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']

		for arrival in stopInfo:
			# Get arrivalTime from JSON content
			arrivalTime = arrival['MonitoredVehicleJourney']['MonitoredCall']['ExpectedArrivalTime']

			# Convert arrivalTime into 12h Pacific time
			utc_datetime = datetime.fromisoformat(arrivalTime[:-1])

			# Define the timezones
			utc_tz = tz.gettz('UTC')
			pacific_tz = tz.gettz('America/Los_Angeles')
			currentTime = datetime.now(timezone.utc)

			# Set the UTC timezone for the datetime object
			utc_datetime = utc_datetime.replace(tzinfo = utc_tz)

			# Convert the datetime object to Pacific time
			pacific_datetime = utc_datetime.astimezone(pacific_tz)

			# Format the datetime object as a 12-hour time string
			time_str = pacific_datetime.strftime('%I:%M %p')
			
			# Calculte timeToArrival
			timeToArrival = pacific_datetime - currentTime
			timeToArrival = divmod(timeToArrival.seconds, 60)
			timeToArrival = f"{str(timeToArrival[0]).rjust(2,'0')}:{str(timeToArrival[1]).rjust(2,'0')}"

			# Get destination from JSON content
			destination = arrival['MonitoredVehicleJourney']['MonitoredCall']['DestinationDisplay']

			# Append [code, direction, time]  to list
			arrivals.append([STOPNAMES[i], DIRECTIONS[i], destination, time_str, timeToArrival, stop])

	# Convert nested list to DataFrame
	arrivals = pd.DataFrame(arrivals, columns=['stopnames', 'direction', 'destination','arrivalTime', 'timeToArrival', 'stopcode'])
	return(arrivals)

# define funciton for writing image and sleeping for 5 min.
def write_to_screen(image, sleep_seconds):
	print('Writing to screen.')
	# Write to screen
	h_image = Image.new('1', (epd.width, epd.height), 255)
	# Open the template
	screen_output_file = Image.open(os.path.join(picdir, image))
	# Initialize the drawing context with template as background
	h_image.paste(screen_output_file, (0, 0))
	epd.init()
	epd.display(epd.getbuffer(h_image))
	# Sleep
	time.sleep(2)
	epd.sleep()
	print('Sleeping for ' + str(sleep_seconds) +'.')
	time.sleep(sleep_seconds)

# define function for displaying error
def display_error(error_source):
	# Display an error
	print('Error in the', error_source, 'request.')
	# Initialize drawing
	error_image = Image.new('1', (epd.width, epd.height), 255)
	# Initialize the drawing
	draw = ImageDraw.Draw(error_image)
	draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
	draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
	current_time = datetime.now().strftime('%H:%M')
	draw.text((300, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
	# Save the error image
	error_image_file = 'error.png'
	error_image.save(os.path.join(picdir, error_image_file))
	# Close error image
	error_image.close()
	# Write error to screen 
	write_to_screen(error_image_file, 30)

# Set the fonts
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)
# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'

# Initialize and clear screen
print('Initializing and clearing screen.')
epd.init()
epd.Clear()

WEATHER_API_KEY = os.environ['OPENWEATHER_API_KEY']
LOCATION = 'San Francisco, CA.'
LATITUDE = os.environ['LATITUDE']
LONGITUDE = os.environ['LONGITUDE']
UNITS = 'imperial'
CSV_OPTION = False # if csv_option == True, a weather data will be appended to 'record.csv'

WEATHER_URL = 'http://api.openweathermap.org/data/2.5/onecall?' 

while True:
	# Ensure there are no errors with connection
	error_connect = True
	while error_connect == True:
		try:
			# HTTP request
			print('Attempting to connect to OWM.')
			response = requests.get(WEATHER_URL, params = {'lat': LATITUDE,
			   											  'long': LONGITUDE,
														  'units': UNITS,
														  'appid': WEATHER_API_KEY})
			print('Connection to OWM successful.')
			error_connect = None
		except:
			# Call function to display connection error
			print('Connection error.')
			display_error('CONNECTION') 
	
	error = None
	while error == None:
		# Check status of code request
		if response.status_code == 200:
			print('Connection to Open Weather successful.')
			# get data in jason format
			data = response.json()
			
			# get current dict block
			current = data['current']
			# get current
			temp_current = current['temp']
			# get feels like
			feels_like = current['feels_like']
			# get humidity
			humidity = current['humidity']
			# get pressure
			wind = current['wind_speed']
			# get description
			weather = current['weather']
			report = weather[0]['description']
			# get icon url
			icon_code = weather[0]['icon']
			#icon_URL = 'http://openweathermap.org/img/wn/'+ icon_code +'@4x.png'
			
			# get daily dict block
			daily = data['daily']
			# get daily precip
			daily_precip_float = daily[0]['pop']
			#format daily precip
			daily_precip_percent = daily_precip_float * 100
			# get min and max temp
			daily_temp = daily[0]['temp']
			temp_max = daily_temp['max']
			temp_min = daily_temp['min']
			transitArrivals = getNextTransit()
			
			# Append weather data to CSV if csv_option == True
			if CSV_OPTION == True:
				# Get current year, month, date, and time
				current_year = datetime.now().strftime('%Y')
				current_month = datetime.now().strftime('%m')
				current_date = datetime.now().strftime('%d')
				current_time = datetime.now().strftime('%H:%M')
				#open the CSV and append weather data
				with open('records.csv', 'a', newline='') as csv_file:
					writer = csv.writer(csv_file, delimiter=',')
					writer.writerow([current_year, current_month, current_date, current_time,
									 LOCATION,temp_current, feels_like, temp_max, temp_min,
									 humidity, daily_precip_float, wind])
				print('Weather data appended to CSV.')
			
			# Set strings to be printed to screen
			string_location = LOCATION
			string_temp_current = format(temp_current, '.0f') + u'\N{DEGREE SIGN}F'
			string_feels_like = 'Feels like: ' + format(feels_like, '.0f') +  u'\N{DEGREE SIGN}F'
			string_humidity = 'Humidity: ' + str(humidity) + '%'
			string_wind = 'Wind: ' + format(wind, '.1f') + ' MPH'
			string_report = 'Now: ' + report.title()
			string_temp_max = 'High: ' + format(temp_max, '>.0f') + u'\N{DEGREE SIGN}F'
			string_temp_min = 'Low:  ' + format(temp_min, '>.0f') + u'\N{DEGREE SIGN}F'
			string_precip_percent = 'Precip: ' + str(format(daily_precip_percent, '.0f'))  + '%'

			string_transit1 = f" City: {transitArrivals.loc[0, 'arrivalTime']}"
			string_transit2 = f"Next: {transitArrivals.loc[1, 'arrivalTime']}"
			
			# Set error code to false
			error = False
			
			'''
			print('Location:', LOCATION)
			print('Temperature:', format(temp_current, '.0f'), u'\N{DEGREE SIGN}F') 
			print('Feels Like:', format(feels_like, '.0f'), 'F') 
			print('Humidity:', humidity)
			print('Wind Speed:', format(wind_speed, '.1f'), 'MPH')
			print('Report:', report.title())
			
			print('High:', format(temp_max, '.0f'), 'F')
			print('Low:', format(temp_min, '.0f'), 'F')
			print('Probabilty of Precipitation: ' + str(format(daily_precip_percent, '.0f'))  + '%')
			'''    
		else:
			# Call function to display HTTP error
			display_error('HTTP')

	# Open template file
	template = Image.open(os.path.join(picdir, 'template.png'))
	# Initialize the drawing context with template as background
	draw = ImageDraw.Draw(template)
	
	# Draw top left box
	## Open icon file
	icon_file = icon_code + '.png' 
	icon_image = Image.open(os.path.join(icondir, icon_file))
	### Paste the image
	template.paste(icon_image, (40, 15))
	## Place a black rectangle outline
	draw.rectangle((25, 20, 225, 180), outline=black)
	## Draw text
	draw.text((30, 200), string_report, font=font22, fill=black)
	draw.text((30, 240), string_precip_percent, font=font30, fill=black)
	# Draw top right box
	draw.text((375, 35), string_temp_current, font=font160, fill=black)
	draw.text((350, 210), string_feels_like, font=font50, fill=black)
	# Draw bottom left box
	draw.text((35, 325), string_temp_max, font=font50, fill=black)
	draw.rectangle((170, 385, 265, 387), fill=black)
	draw.text((35, 390), string_temp_min, font=font50, fill=black)
	# Draw bottom middle box {first was string_humidity, second was string_wind}
	draw.text((345, 340), string_transit1, font=font30, fill=black)
	draw.text((345, 400), string_transit2, font=font30, fill=black)
	# Draw bottom right box
	draw.text((627, 330), 'UPDATED', font=font35, fill=white)
	current_time = datetime.now().strftime('%H:%M')
	draw.text((627, 375), current_time, font = font60, fill=white)

	## Add a reminder to take out trash on Mon and Thurs
	weekday = datetime.today().weekday()
	if weekday == 0 or weekday == 3:
		draw.rectangle((345, 13, 705, 55), fill =black)
		draw.text((355, 15), 'TAKE OUT TRASH TODAY!', font=font30, fill=white)
		
	# Save the image for display as PNG
	screen_output_file = os.path.join(picdir, 'screen_output.png')
	template.save(screen_output_file)
	# Close the template file
	template.close()
	
	# Refresh clear screen to avoid burn-in at 3:00 AM
	if datetime.now().strftime('%H') == '03':
		print('Clearning screen to avoid burn-in.')
		epd.Clear()
	
	# Write to screen
	write_to_screen(screen_output_file, 600)
