import os
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

def login(username, password):
    session = requests.Session()
    session.get(login_url)
    global csrftoken
    csrftoken = session.cookies['csrftoken']

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": login_url
    }

    payload = {
        "csrfmiddlewaretoken": csrftoken,
        "login": username,
        "password": password
    }

    session.post(login_url, data=payload, headers=headers)

    return session

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

def getAllSubmissions(session):
    print('Fetching all successful submissions...', flush=True)
    cached_submissions = []
    if os.path.exists('ez_cache_xD.json') and os.path.isfile('ez_cache_xD.json'):
        with open('ez_cache_xD.json') as json_data_file:
            cache = json.load(json_data_file)
            cached_submissions = cache['cached_submissions']
    new_submissions = []
    got_all_new_submissions = False
    page = 0
    res_per_page = 20
    all_problems = []

    while True:
        offset = page * res_per_page
        response = session.get(submissions_url + '?offset=' + str(offset) + '&limit=' + str(res_per_page))
        res_json = response.json()
        problems = res_json['submissions_dump']
        for problem in problems:
            if problem['status_display'] == 'Accepted':
                if len(cached_submissions) and problem['id'] == cached_submissions[-1]['id_number']:
                    got_all_new_submissions = True
                    break
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
                new_submissions.append(submission)
                print('Retrieved submission for ' + submission['question'], flush=True)
        if got_all_new_submissions or not res_json['has_next']:
            break
        page += 1
        time.sleep(2)

    new_submissions.reverse()
    submissions = cached_submissions + new_submissions
    cache = {
        "cached_submissions": submissions
    }
    with open('ez_cache_xD.json', 'w+') as outfile:
        json.dump(cache, outfile)

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

def getRuntimeSummary(runtime, runtime_percentile):
    summary = 'Runtime: ' + runtime
    if runtime_percentile:
        summary += ' (beats ' + runtime_percentile + '% of submissions)'
    return summary + '\n'

def getMemorySummary(memory):
    return 'Memory: ' + memory + '\n'
            

def createCodeFilesFromSubmissions(submissions, output_directory, chromedriver_path, username, password):
    print('Creating files...', flush=True)
    extensions = {
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
    comment_char = {
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

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
        print('Created output directory', flush=True)

    addNumberingToTitles(submissions)
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
        extension = extensions[language]
        joined_output_directory = os.path.join(output_directory, language)

        if not os.path.exists(joined_output_directory):
            os.mkdir(joined_output_directory)

        file_name = title + '.' + extension
        full_path = os.path.join(joined_output_directory, file_name)

        if os.path.exists(full_path) and os.path.isfile(full_path):
            numFilesSkipped += 1
            print('Skipping ' + file_name + ' -- file already exists', flush=True)
            continue

        if chromedriver_path and not driver:
            print('Using chromedriver')
            driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
            loginDriver(driver, username, password)
        
        runtime_percentile = None
        if driver:
            print('Getting runtime percentile for ' + sub['question'] + '...')
            driver.get(leetcode_base_url + sub['link'])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.ace_line_group'))
            )
            try:
                runtime_percentile = re.findall("\d+\.\d+", driver.find_element_by_css_selector('#runtime_detail_plot_placeholder > div.jquery-flot-comment > div > div').text)[0]
            except:
                pass
        runtime_summary = comment_char[language] + ' ' + getRuntimeSummary(runtime, runtime_percentile)
        memory_summary = comment_char[language] + ' ' + getMemorySummary(memory) + '\n'
        f = open(os.path.join(output_directory, language, file_name), 'w+', encoding='utf-8')
        f.write(runtime_summary)
        f.write(memory_summary)
        f.write(code)
        f.close()
        numFilesCreated += 1
        print('Created file for ' + file_name + ' (' + str(i+1) + '/' + str(numSubmissions) + ')', flush=True)
    print('Created ' + str(numFilesCreated) + ' new files, skipped ' + str(numFilesSkipped) + ' files', flush=True)

def main():
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)
    username = config['leetcode']['username']
    output_directory = config['output_directory_path']
    try:
        chromedriver_path = config['chromedriver_path']
    except:
        chromedriver_path = None
    password = getpass.getpass(prompt='Leetcode password: ')

    session = login(username, password)
    all_submissions_chronological = getAllSubmissions(session)
    createCodeFilesFromSubmissions(all_submissions_chronological, output_directory, chromedriver_path, username, password)
    print('Success! Exiting program', flush=True)


if __name__ == "__main__":
    main()