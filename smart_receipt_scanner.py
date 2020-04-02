import getopt
import os
import re
import string
import subprocess
import sys
from pathlib import Path

import pandas as pd
from PIL import Image
from pytesseract import image_to_string


class Lidl():
    begin = 'CHF'
    finish = 'Totale'


class Migros():
    begin = 'CHF'
    finish = 'TOTALE'


def check_dir(directory):
    """
    Check if the path is a directory, if not create it.
    :param directory: path to the directory
    """
    os.makedirs(directory, exist_ok=True)


def isfloat(value):
    """
    Check if a string value is a float and return a boolean.
    :param value: can be a number or a string
    :return: True if the parameter is a float, False otherwise
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def replace_multiple(main_string, to_be_replaced, new_string):
    """
    Replace a set of multiple sub strings with a new string in main string.
    :param main_string: original string
    :param to_be_replaced: list of character to replace
    :param new_string: the character / string with which to replace the old ones
    :return: the original string without the character occurrences
    """

    # Iterate over the strings to be replaced
    for elem in to_be_replaced:
        # Check if string is in the main string
        if elem in main_string:
            # Replace the string
            main_string = main_string.replace(elem, new_string)

    return main_string


def search_multiple(main_string, to_search):
    """
    Replace a set of multiple sub strings with a new string in main string.
    :param main_string: original string
    :param to_search: list of character to search
    :return: a boolean value, True if the character is found, False otherwise
    """

    # Iterate over the strings to be replaced
    for elem in to_search:
        # Check if string is in the main string
        if elem in main_string:
            # Replace the string
            return True

    return False


def binarize_image(im, store):
    """
    :param im: image
    :param store: store to which the receipt refers
    :return: image preprocessed
    """
    if store == Lidl:
        for i in range(im.size[0]):
            for j in range(im.size[1]):
                if im.getpixel((i, j)) > 170:
                    im.putpixel((i, j), 255)
                else:
                    im.putpixel((i, j), 0)

    return im


def generate_text(lines, path_text_out, puntuaction, store):
    """
    Generate a text file containing the receipt data
    :param lines: receipt lines
    :param path_text_out: path to the output text file
    :param puntuaction: stop symbols to remove
    :param store: store to which the receipt refers

    """
    b = re.compile(store.begin)
    f = re.compile(store.finish)
    start = False
    end = False

    with open(path_text_out, "w") as text_file:
        for line in lines:
            if not line.strip():
                continue

            while not start:
                if re.search(b, line):
                    start = True
                    break
                else:
                    break

            while not end:
                if re.search(f, line):
                    end = True
                    start = None
                    break
                else:
                    break

            if start:
                if line.startswith(store.begin):
                    continue

                if store is Lidl:
                    if line[0].isdigit():
                        continue

                if search_multiple(line, list(puntuaction)):
                    line = replace_multiple(line, list(puntuaction), '')

                text_file.writelines(line)
                text_file.writelines('\n')

            if end:
                text_file.writelines(line)
                text_file.writelines('\n')
                break


def generate_csv(path_csv_out, path_text_out, store):
    """
    Generate the final csv file containing a list of products and prices
    :param path_csv_out: path to the output csv file
    :param path_text_out: path to the output text file
    :param store: store to which the receipt refers
    """
    product = []
    price = []

    with open(path_text_out, "r") as text_file:
        for line in text_file:
            if store is Migros:
                if line[0].isdigit():
                    price[-1] = line.split()[-2]
                    continue

                if line.startswith('AZIONE'):
                    p = re.split(r'(\d+)', line)[0]
                    discount = float(replace_multiple(line, [p, '\n'], '').split()[0])
                    total = round(float(price[-1].split()[0]), 2)
                    price[-1] = str(total - discount)
                    continue

            p = re.split(r'(\d+)', line)[0]
            if store is Lidl:
                if len(p) < 3:
                    continue

            product.append(p)
            cost = replace_multiple(line, [p, '\n'], '')
            if isfloat(cost.split()[0]):
                price.append(cost.split()[0])
            else:
                price.append(cost.split()[1])

    # Get the list of tuples from two lists and merge them by using zip().
    list_of_tuples = list(zip(product, price))

    # Converting lists of tuples into pandas Dataframe.
    df = pd.DataFrame(list_of_tuples, columns=['Product', 'Price'])
    df.to_csv(path_csv_out)


def run(im, path_text_out, path_csv_out, store):
    """
    :param im: image
    :param path_text_out: path to the output text file
    :param path_csv_out: path to the output csv file
    :param store: store to which the receipt refers

    """

    # The original image should be taken with scanbot without flash, shadows and with neutral background
    im = binarize_image(im, store)

    # It is possible to change the language of the receipt. If any language is specified, english is used as default.
    receipt_text = image_to_string(im, lang='ita')
    lines = receipt_text.split('\n')

    puntuaction = replace_multiple(string.punctuation, ['.', ','], '')

    generate_text(lines, path_text_out, puntuaction, store)

    generate_csv(path_csv_out, path_text_out, store)


def main(argv):
    """
    :param argv: command line argument
    """
    inputfile = ''

    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('smart_receipt_scanner.py -i <inputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('smart_receipt_scanner.py -i <inputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg

    # Open the input image and detect to which store the receipt refers to.
    # WIP: actually, only Migros and Lidl are detected.
    im = Image.open(inputfile).convert('L')
    receipt_text = image_to_string(im, lang='ita')

    if 'MIGROS' in receipt_text:
        store = Migros
    else:
        store = Lidl

    # Create the directories for the output file, if do not exist.
    csv_out_dir = 'out/csv/'
    txt_out_dir = 'out/txt/'

    check_dir(csv_out_dir)
    check_dir(txt_out_dir)

    extension = ('.jpg', '.JPG', '.png', '.PNG')
    image_name = Path(inputfile).name

    path_text_out = os.path.join(txt_out_dir, replace_multiple(image_name, extension, '.txt'))
    path_csv_out = os.path.join(csv_out_dir, replace_multiple(image_name, extension, '.csv'))

    try:
        run(im, path_text_out, path_csv_out, store)
        print('Generated ' + path_csv_out)
    except:
        print('Retake the photo ' + inputfile)

    subprocess.call(['open', path_csv_out])


if __name__ == "__main__":
    main(sys.argv[1:])
