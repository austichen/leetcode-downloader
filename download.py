import os
import sys
import re
import json
import getpass
import requests
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

leetcode_base_url = 'https://leetcode.com'
login_url = leetcode_base_url + '/accounts/login'
submissions_url = leetcode_base_url + '/api/submissions/'
csrftoken = ''

chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument('--disable-gpu')  # apparently necessary for headless

session = None
driver = None

config = {}

COMMENT_CHAR = {
    'bash': '#',
    'c': '//',
    'cpp': '//',
    'csharp': '//',
    'golang': '//',
    'java': '//',
    'javascript': '//',
    'mysql': '#',
    'python': '#',
    'python3': '#',
    'ruby': '#',
    'scala': '//',
    'swift': '//',
}

def login(username, password):
    leetcode_session = requests.Session()
    leetcode_session.get(login_url)
    global csrftoken
    csrftoken = leetcode_session.cookies['csrftoken']

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": login_url
    }

    payload = {
        "csrfmiddlewaretoken": csrftoken,
        "login": username,
        "password": password
    }

    leetcode_session.post(login_url, data=payload, headers=headers)

    global session
    session = leetcode_session

def loginDriver(driver, username, password):
    print('Logging in...', flush=True)
    driver.get(login_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-cy="sign-in-btn"]'))
    )
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div#initial-loading'))
    )
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-cy="sign-in-btn"]'))
    )
    email_field = driver.find_element_by_css_selector('input[name="login"]')
    password_field = driver.find_element_by_css_selector('input[name="password"]')
    submit_button = driver.find_element_by_css_selector('button[data-cy="sign-in-btn"]')

    email_field.send_keys(username)
    password_field.send_keys(password)
    submit_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#home-app'))
    )
    print('Login successful', flush=True)

def getCachedSubmissions():
    cached_submissions = []
    if os.path.exists('ez_cache_xD.json') and os.path.isfile('ez_cache_xD.json'):
        with open('ez_cache_xD.json') as json_data_file:
            cache = json.load(json_data_file)
            cached_submissions = cache['cached_submissions']
    return cached_submissions

def updateCachedSubmissions(submissions):
    cache = {
        "cached_submissions": submissions
    }
    with open('ez_cache_xD.json', 'w+') as outfile:
        json.dump(cache, outfile)

def getSubmissionsFromApi(offset, limit):
    response = session.get(submissions_url + '?offset=' + str(offset) + '&limit=' + str(limit))
    res_json = response.json()
    return res_json

def getAcceptedProblemsFromJson(json):
    if 'submissions_dump' not in json:
        print('Login error: incorrect username/password')
        sys.exit()
    return list(filter(lambda p: p['status_display'] == 'Accepted', json['submissions_dump']))

def isProblemCached(problem, cached_submissions):
    return len(cached_submissions) and problem['id'] == cached_submissions[-1]['id_number']

def formatProblem(problem):
    submission = {
        'time_submitted': problem['timestamp'],
        'question': problem['title'],
        'status': "Accepted",
        'runtime': problem['runtime'],
        'memory': problem['memory'],
        'language': problem['lang'],
        'link': problem['url'],
        'id_number': problem['id'],
        'code': problem['code']
    }
    return submission


def getAllSubmissions():
    print('Fetching all successful submissions...', flush=True)
    cached_submissions = getCachedSubmissions()
    new_submissions = []

    got_all_new_submissions = False
    page = 0
    RES_PER_PAGE = 20

    while True:
        offset = page * RES_PER_PAGE
        res_json = getSubmissionsFromApi(offset, RES_PER_PAGE)
        accepted_problems = getAcceptedProblemsFromJson(res_json)
        for problem in accepted_problems:
            if isProblemCached(problem, cached_submissions):
                got_all_new_submissions = True
                break
            submission = formatProblem(problem)
            new_submissions.append(submission)
            print('Retrieved submission for ' + submission['question'], flush=True)
        if got_all_new_submissions or not res_json['has_next']:
            break
        page += 1
        time.sleep(2) # api calls are rate limited

    new_submissions.reverse() # put in chronological order
    submissions = cached_submissions + new_submissions
    updateCachedSubmissions(submissions)

    print('Fetched ' + str(len(new_submissions)) + ' new submissions, retrieved ' + str(len(cached_submissions)) + ' submissions from cache', flush=True)
    return submissions

def addNumberingToTitles(submissions):
    print('Numbering duplicate submissions...', flush=True)
    numTimesSeen = {}
    for i in range(len(submissions)):
        sub = submissions[i]
        question = sub['question']
        language = sub['language']
        if question in numTimesSeen and language in numTimesSeen[question]:
            numTimesSeen[question][language] += 1
            submissions[i]['question'] = question + ' [' + str(numTimesSeen[question][language]) + ']'
        else:
            if question not in numTimesSeen:
                numTimesSeen[question] = {}
            if language not in numTimesSeen[question]:
                numTimesSeen[question][language] = 1
    print('Numbering completed', flush=True)

def createDirectory(path):
    if not os.path.exists(path):
        os.mkdir(path)
        print('Created directory ' + path, flush=True)

def createCodeFile(path, runtime_summary, memory_summary, code):
    f = open(path, 'w+', encoding='utf-8')
    f.write(runtime_summary)
    f.write(memory_summary)
    f.write(code)
    f.close()

def getRuntimePercentile(question, link):
    if 'chromedriver_path' not in config:
        return None

    global driver
    if not driver:
        print('Using chromedriver')
        driver = webdriver.Chrome(config['chromedriver_path'], options=chrome_options)
        try:
            loginDriver(driver, config['leetcode']['username'], config['leetcode']['password'])
        except Exception as e:
            print(e)
            driver.close()

    runtime_percentile = None
    print('Getting runtime percentile for ' + question + '...')
    try:
        driver.get(link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ace_line_group'))
        )
        runtime_percentile = re.findall("\d+\.\d+", driver.find_element_by_css_selector('#runtime_detail_plot_placeholder > div.jquery-flot-comment > div > div').text)[0]
    except:
        pass
    return runtime_percentile

def getRuntimeSummary(language, runtime, runtime_percentile):
    summary = COMMENT_CHAR[language] + ' ' + 'Runtime: ' + runtime
    if runtime_percentile:
        summary += ' (beats ' + runtime_percentile + '% of submissions)'
    return summary + '\n'

def getMemorySummary(language, memory):
    return COMMENT_CHAR[language] + ' ' + 'Memory: ' + memory + '\n'
            

def createCodeFilesFromSubmissions(submissions):
    print('Creating files...', flush=True)
    EXTENSIONS = {
        'bash': 'sh',
        'c': 'c',
        'cpp': 'cpp',
        'csharp': 'cs',
        'golang': 'go',
        'java': 'java',
        'javascript': 'js',
        'mysql': 'sql',
        'python': 'py',
        'python3': 'py',
        'ruby': 'rb',
        'scala': 'scala',
        'swift': 'swift',
    }

    createDirectory(config['output_directory_path'])

    numSubmissions = len(submissions)
    numFilesCreated = 0
    numFilesSkipped = 0
    driver = None
    
    for i in range(len(submissions)):
        sub = submissions[i]
        title = sub['question']
        language = sub['language']
        code = sub['code']
        runtime = sub['runtime']
        memory = sub['memory']

        language_folder = os.path.join(config['output_directory_path'], language)
        createDirectory(language_folder)

        file_name = title + '.' + EXTENSIONS[language]
        file_path = os.path.join(language_folder, file_name)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            numFilesSkipped += 1
            print('Skipping ' + file_name + ' -- file already exists', flush=True)
            continue
        
        runtime_percentile = getRuntimePercentile(title, leetcode_base_url + sub['link'])
        runtime_summary = getRuntimeSummary(language, runtime, runtime_percentile)
        memory_summary = getMemorySummary(language, memory) + '\n'

        createCodeFile(os.path.join(config['output_directory_path'], language, file_name), runtime_summary, memory_summary, code)
        numFilesCreated += 1

        print('Created file for ' + file_name + ' (' + str(i+1) + '/' + str(numSubmissions) + ')', flush=True)
    print('Created ' + str(numFilesCreated) + ' new files, skipped ' + str(numFilesSkipped) + ' files', flush=True)

def download():
    global config
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)
    config['leetcode']['password'] = getpass.getpass(prompt='Leetcode password: ')

    login(config['leetcode']['username'], config['leetcode']['password'])
    all_submissions_chronological = getAllSubmissions()
    addNumberingToTitles(all_submissions_chronological)
    createCodeFilesFromSubmissions(all_submissions_chronological)
    print('Success! Exiting program', flush=True)


if __name__ == "__main__":
    download()