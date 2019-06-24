from flask import Flask, render_template, request, Markup
import requests
import json

app = Flask(__name__)

API_BASE = 'https://developer.nps.gov/api/v1/'
API_KEY = '&api_key=AMyYqj10y2R1aPSgztNfTIB6qVhPCJE1twfW65xK'

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.args.get('query')
    state = request.args.get('state')
    designation = request.args.get('designation')
    if state is None and designation is None:
        state = "ALL STATES"
        designation = "ALL DESIGNATIONS"
    if state == "ALL STATES":
        state_abbrev = ""
    else:
        state_abbrev = STATES[state]
    if designation == "Other":
        designation_q = ""
    else:
        designation_q = designation
    data = call_api('parks', 'q', query, 'stateCode', state_abbrev)
    results_raw = processing_data(data['data'])
    results = []
    if designation != "ALL DESIGNATIONS":
        for park in results_raw:
            if park['designation'] == designation_q:
                results.append(park)
    else:
        results = results_raw
    num_results = int(data['total'])
    return render_template("search_list.html", query = query, results = results,
    num_results = num_results, STATES=STATES, DESIGNATIONS=DESIGNATIONS,
    state = state, designation = designation)

@app.route("/parks/<code>/<section>")
def parks_overview(code, section):
    park = []
    visitorcenters = []
    campgrounds = []
    alerts = []
    articles = []
    events = []
    newsreleases = []
    lessonplans = []
    people = []
    places = []

    # Park general information
    data = call_api('parks', 'parkCode', code)
    results = processing_data(data['data'])
    park = results[0]
    # Visitor centers
    if section == "visitor-centers":
        data = call_api('visitorcenters', 'parkCode', code)
        visitorcenters = data['data']
    # Campgrounds
    if section == "campgrounds":
        data = call_api('campgrounds', 'parkCode', code)
        campgrounds = data['data']
    # Alerts
    if section == "alerts":
        data = call_api('alerts', 'parkCode', code)
        alerts = data['data']
    # Articles
    if section == "articles":
        data = call_api('articles', 'parkCode', code)
        articles = data['data']
    # Events
    if section == "events":
        data = call_api('events', 'parkCode', code)
        events = clean_up_tags(data['data'])
    # News releases
    if section == "news-releases":
        data = call_api('newsreleases', 'parkCode', code)
        newsreleases = data['data']
    # Education
    if section == "education":
        data = call_api('lessonplans', 'parkCode', code)
        lessonplans = data['data']
        data = call_api('people', 'parkCode', code)
        people = data['data']
        data = call_api('places', 'parkCode', code)
        places = data['data']

    return render_template("park.html", park = park, visitorcenters = visitorcenters,
    campgrounds = campgrounds, alerts = alerts, articles = articles, events = events,
    newsreleases = newsreleases, lessonplans = lessonplans, people = people,
    places = places, code = code, section = section)

def call_api(category, parameter_1, value_1, parameter_2='', value_2='', parameter_3='', value_3=''):
    # Valid category: parks, campgrounds, ...
    url = API_BASE + category + '?' + parameter_1 + '=' + value_1
    if parameter_2 != '' and value_2 != '':
        url += '&' + parameter_2 + '=' + value_2
    if parameter_3 != '' and value_3 != '':
        url += '&' + parameter_3 + '=' + value_3
    url += API_KEY
    response = requests.get(url)
    data = response.json()
    return data

# REQUIRES: data is a list of dictionaries (parks)
def processing_data(data):
    for park in data:
        park['states'] = park['states'].replace(',',', ')
        if park['fullName'] == 'Kaloko-Honok&#333;hau National Historical Park':
            park['fullName'] = 'Kaloko-Honokohau National Historical Park'
        if park['designation'] == '':
            park['designation'] = 'Other'
    return data

# REQUIRES: data is a list of dictionaries (events)
def clean_up_tags(data):
    for event in data:
        event['description'] = Markup(event['description'])
    return data

def load_states():
    with open('./static/json/states.json') as json_file:
        return json.load(json_file)

def load_designations():
    data = call_api('parks', 'q', '')
    list = []
    for park in data['data']:
        if park['designation'] == "":
            park['designation'] = "Other"
        if park['designation'] not in list:
            list.append(park['designation'])
    return list

STATES = load_states()

DESIGNATIONS = load_designations()
print DESIGNATIONS

if __name__ == "__main__":
    app.debug = True
    app.run()
