from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import os
import re
import json

leetcode_base_url = 'https://leetcode.com'
login_url = leetcode_base_url + '/accounts/login/?next=/submissions/#/1'

chrome_options = Options()  
chrome_options.add_argument("--headless")  
chrome_options.add_argument('--disable-gpu')  # apparently necessary for headless

def login(driver, username, password):
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
        EC.presence_of_element_located((By.CSS_SELECTOR, '#submission-list-app'))
    )
    print('Login successful', flush=True)


def getAllSubmissions(driver):
    print('Fetching all successful submissions...', flush=True)
    cached_submissions = []
    if os.path.exists('ez_cache_xD.json') and os.path.isfile('ez_cache_xD.json'):
        with open('ez_cache_xD.json') as json_data_file:
            cache = json.load(json_data_file)
            cached_submissions = cache['cached_submissions']
    new_submissions = []
    got_all_new_submissions = False
    while True:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody > tr'))
        )
        submissions_html = driver.find_elements_by_css_selector('tbody > tr')
        for sub in submissions_html:
            children = sub.find_elements_by_css_selector('td')
            time_submitted = children[0].text
            question = children[1].text
            status = children[2].text
            runtime = children[3].text
            language = children[4].text
            if status == 'Accepted':
                link = children[2].find_element_by_css_selector('a').get_attribute('href')
                id_number = link.split('/')[-2]
                if len(cached_submissions) and id_number == cached_submissions[-1]['id_number']:
                    got_all_new_submissions = True
                    break
                submission = {
                    'time_submitted': time_submitted,
                    'question': question,
                    'status': status,
                    'runtime': runtime,
                    'language': language,
                    'link': link,
                    'id_number': id_number
                }
                new_submissions.append(submission)
                print('Retrieved submission for ' + question, flush=True)
        if got_all_new_submissions:
            break
        try:
            next_button = driver.find_element_by_css_selector('li.next > a')
            next_button.click()
        except:
            break
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

def getRuntimeSummary(driver):
    runtime = driver.find_element_by_css_selector('#result_runtime').text
    runtime_percentile = re.findall("\d+\.\d+", driver.find_element_by_css_selector('#runtime_detail_plot_placeholder > div.jquery-flot-comment > div > div').text)[0]
    return 'Runtime: ' + runtime + ' (beats ' + runtime_percentile + '% of submissions)\n'

def getMemorySummary(driver):
    memory = driver.find_element_by_css_selector('#result_memory').text
    return 'Memory: ' + memory + '\n'
            

def createCodeFilesFromSubmissions(driver, submissions, output_directory):
    print('Creating files...', flush=True)
    extensions = {
        'python3': 'py',
        'python': 'py',
        'java': 'java',
        'javascript': 'js',
        'c': 'c',
        'cpp': 'cpp'
    }
    comment_char = {
        'python3': '#',
        'python': '#',
        'java': '//',
        'javascript': '//',
        'c': '//',
        'cpp': '//'
    }

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
        print('Created output directory', flush=True)

    addNumberingToTitles(submissions)
    numSubmissions = len(submissions)
    numFilesCreated = 0
    numFilesSkipped = 0
    
    for i in range(len(submissions)):
        sub = submissions[i]
        title = sub['question']
        language = sub['language']
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

        driver.get(sub['link'])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ace_line_group'))
        )
        code_lines = driver.find_elements_by_css_selector('.ace_line_group')
        runtime_summary = ''
        memory_summary = ''
        try:
            runtime_summary = comment_char[language] + ' ' + getRuntimeSummary(driver)
            memory_summary = comment_char[language] + ' ' + getMemorySummary(driver) + '\n'
        except:
            pass
        f = open(os.path.join(output_directory, language, file_name), 'w+')
        f.write(runtime_summary)
        f.write(memory_summary)
        for line in code_lines:
            f.write(line.text + '\n')
        f.close()
        numFilesCreated += 1
        print('Created file for ' + file_name + ' (' + str(i+1) + '/' + str(numSubmissions) + ')', flush=True)
    print('Created ' + str(numFilesCreated) + ' new files, skipped ' + str(numFilesSkipped) + ' files', flush=True)

def main():
    print('Loading config', flush=True)
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)
    username = config['leetcode']['username']
    password = config['leetcode']['password']
    output_directory = config['output_directory_path']

    print('Starting webdriver...', flush=True)
    driver = webdriver.Chrome(config['chromedriver_path'], options=chrome_options)
    try:
        login(driver, username, password)
        all_submissions_chronological = None
        all_submissions_chronological = getAllSubmissions(driver)
        createCodeFilesFromSubmissions(driver, all_submissions_chronological, output_directory)
        print('Success! Exiting program', flush=True)
    finally:
        driver.close()


if __name__ == "__main__":
    main()