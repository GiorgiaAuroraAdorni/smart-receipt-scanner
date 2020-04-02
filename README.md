# smart-receipt-scanner

**Smart receipt scanner** is an easy converter of invoices or receipt images into an csv file containing a list of products and prices.

### Feature

The script is able to work with images already cropped and of good quality, for example generated with smartphone scanning app.

Now we support two grocery stores in Switzerland, Italy, Germany etc.

The current version support many languages but uses Italian as default. In order to change the receipt language modify the parameter`lan` in the current line `receipt_text = image_to_string(im, lang='ita')` .

### Prerequisites

> Python 3, Pip, Homebrew

For macOS, using homebrew, run:

```sh
$ brew install tesseract
$ brew install tesseract-lang
```

### Installation

Clone the repository

```sh
$ git clone https://github.com/GiorgiaAuroraAdorni/smart-receipt-scanner
$ cd smart-receipt-scanner
```

The `requirements.txt` file list all Python libraries that you need to install. Execute:

```sh
$ pip3 install -r requirements.txt
```

### Usage

To receive help on how to run the script, execute

```sh
$ python3 smart_receipt_scanner.py -h
```

To execute the script

```sh
$ python3 smart_receipt_scanner.py -i <inputfile>
```