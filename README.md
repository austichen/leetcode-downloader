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
2. Move `chromedriver.exe` executable to a directory of your choice. If you want to keep it simple, move it into this folder
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
