# Leetcode Downloader

A simple python script to download your (successful) Leetcode submissions to your computer

## Usage

### Clone Repo
```
git clone https://github.com/austichen/leetcode-downloader.git
cd leetcode-downloader
```
### Create your config file
```
cp config.default.json config.json
```
- `username`: Enter your Leetcode username here
- `output_directory_path`: The path you would like to output the files to. You can use the default value

### Install dependencies
```
pip install requests
pip install selenium
```

### Run script

Make sure you're on `Python 3.x`, then run
```
python download.py
```

Enter your password when prompted. After the script finishes, check the `output_directory_path` folder you specified, and all your successfull submissions should be there! If you re-run the script multiple times, it will only fetch the new submissions that you haven't downloaded yet.

**Note**: If you're using `git bash` on windows, and the script hangs (the prompt to enter your password doesn't show up), you may need to set up an alias to your python executable. Just run this command: `alias python='winpty python.exe'` before running `python download.py`

## Extra Notes

### Runtime Percentile

By default, the script will add the `runtime` and `memory` as comments at the top of each file, like this:
```python
# Runtime: 40 ms
# Memory: 13.8 MB

class Solution:
    solution...
```

There is a way to configure the script to add the `runtime percentile` of your program to the comments as well, like this:
```python
# Runtime: 40 ms (beats 95.47% of submissions)
# Memory: 13.8 MB

class Solution:
    solution...
```

If you want to have the `runtime percentile` added, perform the following steps:
1. Download the correct version of [`chromedriver`](https://chromedriver.chromium.org/downloads) for your computer and chrome version
2. Extract the `chromedriver.exe` executable to a directory of your choice. If you want to keep it simple, move it into this folder
3. Add the `chromedriver_path` key to your `config.json`:
```
"chromedriver_path": "path/to/chromedriver.exe"
```
For example, if you moved `chromedriver.exe` to this folder, your `config.json` should look like this:
```json
{
    "leetcode": {
        "username": "youremail@email.com"
    },
    "output_directory_path": "submission_files",
    "chromedriver_path": "chromedriver.exe"
}
```

Note: It will take significantly longer for the script to run if you enable `runtime percentile`s, but it's pretty worth

### Push to Github

If you connect your `output_directory_path` folder with a Github remote, you can also automatically push your submission files to your Github repo by adding the `--github` flag:
```
python download.py --github
```

To set this up, perform the following steps:

1. Create a new repository on Github. Copy the Git URL for the new repo.
2. Initialize your output directory with Git and set its remote to your new repository:
```
cd <path/to/your_output_directory>
git init
git remote add origin <git_url_you_copied>
```
3. Run the script with the `--github` tag
```
python download.py --github
```
4. If you check your Github repository, your files should now be there!