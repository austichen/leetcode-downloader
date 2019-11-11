# Leetcode Downloader

A simple python script to download your (successful) Leetcode submissions to your computer

## Usage

### Download chromedriver
- Download the correct version of [`chromedriver`](https://chromedriver.chromium.org/downloads) for your computer
- Move `chromedriver.exe` to a directory of your choice. If you want to keep it simple, you can move it into this folder

### Create your config file
```
cp config.default.json config.json
```
- Replace the `username` and `password` fields with your own Leetcode login credentials
- If you want, change the `output_directory_path` to the path you would like to output the files to (ie `D:/leetcode-solutions`, `~/Documents/leetcode-solutions`)
- If your `chromedriver.exe` file is not in this folder, change the `chromedriver_path` to the correct path to your `chromedriver.exe` file

### Install dependencies
```
pip install selenium
```

### Run script

Make sure you're on `Python 3.x`, then run
```
python download.py
```

Check your `output_directory_path` folder, and all your successfull submissions should be there!

