import requests

#parses course descriptions from various natural language formats into correct format for URL
#e.g. ARAB 101, ARAB101, Arabic 101 should map to {subject: 'ARAB', number: '101'}
def parseDescription(shortDescription):
    shortDescription = shortDescription.strip()

    departmentString = ''
    courseNumber = ''

    for character in shortDescription:
        if
