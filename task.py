import requests
from lxml import html, etree
from io import BytesIO
from PIL import Image
import json

url = 'https://parivahan.gov.in/rcdlstatus/?pur_cd=101'
driving_license = input("Enter DL number (format : DL-xxxxxxxxxxxxx): ")

#assuming the dob is not entered in wrong format
dob = input("Enter date of birth in dd-mm-yyyy format: ")

#function to display the captcha and fill it manually
def get_captcha(tree):
	captcha = tree.xpath('//*[@id="form_rcdl:j_idt37:j_idt45"]')[0].get('src')
	captcha_url = requests.get('https://parivahan.gov.in'+captcha)
	captcha_img = Image.open(BytesIO(captcha_url.content))
	captcha_img.show()
	captcha_code = str(input("enter captcha  - "))
	return captcha_code

#this function takes the login_data and creates a post request, and parses the xml response to return 
#the viewstate for next post request
def post_and_next_viewstate(c, login_data):
	response = c.post(url, data = login_data)	
	tree = etree.fromstring(response.content)
	viewstate = tree.xpath('//update[@id="j_id1:javax.faces.ViewState:0"]/text()')[0]
	return viewstate

success = 0
while(not(success)):
	with requests.Session() as c:
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'}
		
		#get request to extract the 1st viewstate (viewstate changes everytime)
		response = c.get(url, headers = headers)
		tree = html.fromstring(response.content)
		captcha_code = get_captcha(tree)
		viewstate = tree.xpath('//*[@id="j_id1:javax.faces.ViewState:0"]')[0].get('value')
		
		#create the 1st post request and get the next viewstate
		login_data = {
			'javax.faces.partial.ajax': 'true',
			'javax.faces.source': 'form_rcdl:tf_dlNO',
			'javax.faces.partial.execute': 'form_rcdl:tf_dlNO',
			'javax.faces.partial.render': 'form_rcdl:tf_dlNO',
			'javax.faces.behavior.event': 'valueChange',
			'javax.faces.partial.event': 'change',
			'form_rcdl': 'form_rcdl',
			'form_rcdl:tf_dlNO': driving_license ,
			'form_rcdl:tf_dob_input': '',
			'form_rcdl:j_idt37:CaptchaID': '',
			'javax.faces.ViewState': viewstate,
		}
		viewstate = post_and_next_viewstate(c, login_data)

		#2nd post 
		login_data = {
			'javax.faces.partial.ajax': 'true',
			'javax.faces.source': 'form_rcdl:tf_dob',
			'javax.faces.partial.execute': 'form_rcdl:tf_dob',
			'javax.faces.partial.render': 'form_rcdl:tf_dob',
			'javax.faces.behavior.event': 'valueChange',
			'javax.faces.partial.event': 'change',
			'form_rcdl:tf_dob_input': dob,
			'javax.faces.ViewState': viewstate
		}
		viewstate = post_and_next_viewstate(c, login_data)
		
		#3rd post
		login_data = {
			'form_rcdl': 'form_rcdl',
			'form_rcdl:tf_dlNO': driving_license,
			'form_rcdl:tf_dob_input': dob,
			'form_rcdl:j_idt37:CaptchaID': captcha_code,
			'javax.faces.ViewState': viewstate,
			'javax.faces.source': 'form_rcdl:j_idt37:CaptchaID',
			'javax.faces.partial.event': 'blur',
			'javax.faces.partial.execute': 'form_rcdl:j_idt37:CaptchaID',
			'javax.faces.partial.render': 'form_rcdl:j_idt37:CaptchaID',
			'CLIENT_BEHAVIOR_RENDERING_MODE': 'OBSTRUSIVE',
			'javax.faces.behavior.event': 'blur',
			'javax.faces.partial.ajax': 'true'
		}
		viewstate = post_and_next_viewstate(c, login_data)
		
		#4th post request and the final results are obtained
		login_data = {
			'javax.faces.partial.ajax': 'true',
			'javax.faces.source': 'form_rcdl:j_idt50',
			'javax.faces.partial.execute': '@all',
			'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
			'form_rcdl:j_idt50': 'form_rcdl:j_idt50',
			'form_rcdl': 'form_rcdl',
			'form_rcdl:tf_dlNO': driving_license,
			'form_rcdl:tf_dob_input': dob,
			'form_rcdl:j_idt37:CaptchaID': captcha_code,
			'javax.faces.ViewState': viewstate
		}
		response = c.post(url, data = login_data)
		tree = etree.fromstring(response.content)

		#if extension tag exists then wrong captcha
		if(bool(tree.xpath('//changes/extension'))):
			print("wrong captcha")
			continue

		#if eval tag exists then wrong login details
		if(bool(tree.xpath('//changes/eval'))):
			print("wrong login details")	
			break
		
		#extract html from xml and parse it
		html_doc = tree.xpath('//update[@id="form_rcdl:rcdl_pnl"]')[0]
		tree = html.fromstring(html_doc.text)

		#saving the final results
		current_status = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[1]/tr[1]/td[2]/span/text()')[0]
		holder_name = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[1]/tr[2]/td[2]/text()')[0]
		date_of_issue = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[1]/tr[3]/td[2]/text()')[0]
		last_transaction = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[1]/tr[4]/td[2]/text()')[0]
		old_new_DL = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[1]/tr[5]/td[2]/text()')[0]
		non_transport_from = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[2]/tr[1]/td[2]/text()')[0]
		non_transport_to = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[2]/tr[1]/td[3]/text()')[0]
		transport_from = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[2]/tr[2]/td[2]/text()')[0]
		transport_to = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[2]/tr[2]/td[3]/text()')[0]
		hazardous_till = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[3]/tr[1]/td[2]/text()')[0]
		hill_till = tree.xpath('//*[@id="form_rcdl:j_idt123"]/table[3]/tr[1]/td[4]/text()')[0]
		cov_category = tree.xpath('//*[@id="form_rcdl:j_idt181_data"]/tr/td[1]/text()')[0]
		class_of_vehicle = tree.xpath('//*[@id="form_rcdl:j_idt181_data"]/tr/td[2]/text()')[0]
		cov_issue_date = tree.xpath('//*[@id="form_rcdl:j_idt181_data"]/tr/td[3]/text()')[0]

	#create a dictionary from the results
	results = {
		"Current Status": current_status,
		"Holder's Name": holder_name,
		"Date Of Issue": date_of_issue,
		"Last Transaction At": last_transaction,
		"Old / New DL No.": old_new_DL,
		"Non-Transport From": non_transport_from,
		"Non-Transport To": non_transport_to,
		"Transport From": transport_from,
		"Transport To": transport_to,
		"Hazardous Valid Till": hazardous_till,
		"Hill Valid Till": hill_till,
		"COV Category": cov_category,
		"Class Of Vehicle": class_of_vehicle,
		"COV Issue Date": cov_issue_date
	}

	#write the results dict into a json file
	with open('results.json', 'w') as f:
		json.dump(results, f)

	print("results written into results.json file")
	success = 1
