# smart-receipt-scanner

**Smart receipt scanner** is an easy converter of invoices and receipt images into an csv file containing a list of products and prices.

### Features

The script is able to work with images already cropped and of good quality, for example generated with smartphone scanning apps.

Now we support *Migros* and *Lidl* as grocery stores in Switzerland, Italy, Germany etc.

The current version supports many languages but uses Italian as default. In order to change the receipt language, modify the parameter `lan` in the current line: `receipt_text = image_to_string(im, lang='ita')`.

### Prerequisites

> Python 3, Pip, Homebrew

For macOS, using homebrew, run:

```sh
$ brew install tesseract tesseract-lang
```

### Installation

Clone the repository:

```sh
$ git clone https://github.com/GiorgiaAuroraAdorni/smart-receipt-scanner
$ cd smart-receipt-scanner
```

Execute the `requirements.txt` file to install a list of all Python libraries that you need:

```sh
$ pip3 install -r requirements.txt
```

### Usage

To receive help on how to run the script, execute:

```bash
$ python3 smart_receipt_scanner.py -h
```

```bash
> usage: smart_receipt_scanner.py [-h][--image IMAGE] [--txt TXT][--store {migros,lidl}]

	Smart Receipt Scanner

	optional arguments:
  		-h, --help            show this help message and exit
		--image IMAGE         path to the image of the receipt to scan (default: None)
  		--txt TXT             path to the txt containing the receipt (default: None)
  		--store {migros,lidl} choose a store to which the receipt refers between migros 							  and lidl (default: migros)
```

To execute the script:

```bash
$ python3 smart_receipt_scanner.py --image <inputImage>
```

or

```bash
$ python3 smart_receipt_scanner.py --txt <inputFile> [--store lidl]
```

