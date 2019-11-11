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

Check your `output_directory_path` folder, and all your successfull submissions should be there!

