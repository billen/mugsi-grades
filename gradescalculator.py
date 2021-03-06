from pprint import pprint
import sys
import getpass

try:
	import mechanize
except ImportError:
	print "Error: mechanize not found."
	sys.exit(0)

DEBUG = False

GRADE_VALUES = {
	"A+":	12,
	"A":	11,
	"A-":	10,
	"B+":	9,
	"B":	8,
	"B-":	7,
	"C+":	6,
	"C":	5,
	"C-":	4,
	"D+":	3,
	"D":	2,
	"D-":	1,
	"F":	0,
}

def loginToBrowser(username, password):
	global DEBUG
	print "Getting your grades. Please wait... \n\n",
	browser = mechanize.Browser()
	browser.set_handle_robots(False)
	browser.open("https://adweb.cis.mcmaster.ca/cis/ahtml/login.htm")
	browser.select_form(nr = 0)
	browser.form['credential_0'] = username
	browser.form['credential_1'] = password
	browser.submit()
	browser.open("https://adweb.cis.mcmaster.ca/mugsi/fp")
	try:
		browser.select_form(name="myform")
		browser.submit()
		browser._factory.is_html = True
		browser.select_form(name="P002")
		browser.submit()
		browser._factory.is_html = True
		browser.select_form(name="Q004")
		browser.submit()
		browser._factory.is_html = True
		browser.select_form(name="DEGAUD")
		browser.submit()
	except:
		print "Incorrect credentials or connection to MUGSI might be the problem. Exiting program"
		sys.exit()
	response = browser.response().read()
	if browser.response().code == 200:
		cleaned_grades = getGradesFromResponse(response)
		if cleaned_grades:
			return cleaned_grades
		else:
			print "Uh oh! We logged in, but couldn't read the response. Maybe degree audit is down?"
			sys.exit(0)
	else:
		print "Uh oh! Couldn't connect to MUGSI."
		sys.exit(0)

def getGradesFromResponse(response):
	try:
		start = response.index( "<PRE>" ) + len( "<PRE>" )
		end = response.index( "</PRE>", start )
		pre_block = response[start:end]
		# whatchu know about list comprehensions
		grades =[x for x in pre_block.split("\n") if "|" in x]
		cleaned_grades = [[g.strip() for g in grade.split("  ") if g and g != "|"][:6] for grade in grades]
		return cleaned_grades
	except ValueError:
		return

def calculateGrades(grades):
	global DEBUG
	gradedict = {}
	gradedict['term'] = {}
	units = 0.0
	weightedgrades = 0.0
	for grade in grades:
		try:
			grade_unit = int(grade[3])
			weightedgrades = weightedgrades + grade_unit * GRADE_VALUES[grade[4]]
			units = units + grade_unit
		except Exception:
			if DEBUG:
				print "Found bad entry: "+  grade
			else:
				pass
		try:
			if grade[5] not in gradedict['term']:
				gradedict['term'][grade[5]] = []
			gradedict['term'][grade[5]].append(grade)
		except IndexError:
			pass
	gradedict['total'] = weightedgrades/units

	for term in gradedict['term'].keys():
		units 			= 0.0
		weightedgrades  = 0.0
		term_grades 	= gradedict['term'][term]

		for grade in term_grades:
			try:
				grade_unit = int(grade[3])
				weightedgrades = weightedgrades + grade_unit * GRADE_VALUES[grade[4]]
				units = units + grade_unit
			except Exception:
				if DEBUG:
					print "Found bad entry: "+  grade
				else:
					pass
		if 'term_grades' not in gradedict:
			gradedict['term_grades'] = {}
		try:
			gradedict['term_grades'][term[2:]+"/20"+term[:2]] = weightedgrades/units
		except ZeroDivisionError:
			# Current course load 
			pass

	return gradedict

def main():
	print "BetterMUGSI Grade Calculator V1.0"
	MACID = raw_input("Enter your username: ")
	PASSWORD = getpass.getpass("Please enter your password: ")
	if not MACID and not PASSWORD:
		print "Please enter correct credentials. Program exiting"
	else:
		webDATA = loginToBrowser(MACID,PASSWORD)
		gradedict = calculateGrades(webDATA)
		print "TERM     | GRADE"
		print "-------------------"
		keys = gradedict['term_grades'].keys()
		keys.sort(key=lambda x: [int(y) for y in x.split('/')[1]])
		for term in keys:
			print "%s: | %.2f" % (term, round(float(gradedict['term_grades'][term]),2))
		print     "Total:   | %.2f" % (round(gradedict['total'],2),)

main()