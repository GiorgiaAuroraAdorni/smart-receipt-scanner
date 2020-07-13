import argparse
import os
import re
import string
import subprocess
from pathlib import Path

import pandas as pd
from PIL import Image
from pytesseract import image_to_string


class Lidl():
    begin = 'CHF'
    finish = 'Totale'


class Migros():
    begin = 'CHF'
    begin2 = 'MMM Lugano'
    finish = '^TOTALE'


def parse_args():
    parser = argparse.ArgumentParser(description='Smart Receipt Scanner')

    parser.add_argument('--image', default=None, type=str,
                        help='path to the image of the receipt to scan (default: None)')
    parser.add_argument('--txt', default=None, type=str,
                        help='path to the txt containing the receipt (default: None)')
    parser.add_argument('--store', default='migros', choices=['migros', 'lidl'],
                        help='choose a store to which the receipt refers between migros and lidl (default: migros)')

    args = parser.parse_args()

    return args


def check_dir(directory):
    """
    Check if the path is a directory, if not create it.
    :param directory: path to the directory
    """
    os.makedirs(directory, exist_ok=True)


def isprice(value):
    """
    Check if a string value is a price, that means a float with two decimals, and return a boolean.
    :param value: can be a number or a string
    :return: True if the parameter is a float, False otherwise
    """
    try:
        float_regex = '^([0-9]+\\.)[0-9]{2}$'
        if re.match(float_regex, value):
            return True
    except ValueError:
        return False


def isfloat(value):
    """
    Check if a string value is a float and return a boolean.
    :param value: can be a number or a string
    :return: True if the parameter is a float, False otherwise
    """
    try:
        float_regex = '^([0-9]+\\.)[0-9]+$'
        if re.match(float_regex, value):
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
    if store is Migros:
        b2 = re.compile(store.begin2)
    f = re.compile(store.finish)
    start = False
    end = False

    with open(path_text_out, "w") as text_file:
        for line in lines:
            if not line.strip():
                continue

            while not start:
                if store is Migros and re.search(b2, line):
                    start = True
                    break
                elif re.search(b, line):
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

                if store is Migros:
                    if line.startswith(store.begin2):
                        continue
                    if line.startswith('^CUM[0-9]+x'):
                        continue
                    if re.search('MIGROS', line):
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
    products = []
    prices = []

    verify = False

    with open(path_text_out, "r") as text_file:
        for line in text_file:
            stop_pattern = ' ([0-9]|A)\n'
            if re.search(stop_pattern, line):
                stop = re.search(stop_pattern, line)[0]
                line = line.rsplit(stop, 1)[0]

            if verify:
                costs = line.split()

                # Price for kilos
                if isfloat(costs[0]):
                    prices.append(costs[-1])

                # Multiple products
                else:
                    moltiplicator = costs[0]
                    price = costs[-1]
                    cost = float(moltiplicator) * float(price)
                    prices.append('{:.2f}'.format(cost))

                verify = False
                continue

            if store is Migros:
                if line[0].isdigit():
                    prices[-1] = line.split()[-2]
                    continue

                if line.startswith('AZIONE'):
                    p = re.split(r'(\d+)', line)[0]
                    discount = float(replace_multiple(line, [p, '\n'], '').split()[0])
                    total = round(float(prices[-1].split()[0]), 2)
                    prices[-1] = '{:.2f}'.format(float(total - discount))
                    continue

            p = re.split(r'(\d+)', line)[0]

            if store is Lidl:
                if len(p) < 3:
                    continue
                if line.startswith('Sconto'):
                    p = re.split(r'(\d+)', line)[0]
                    discount = float(replace_multiple(line, [p, '\n'], '').split()[-1])
                    total = round(float(prices[-1].split()[0]), 2)
                    prices[-1] = '{:.2f}'.format(float(total - discount))
                    continue

            products.append(p)
            cost = replace_multiple(line, [p, '\n'], '')

            if cost == "":
                verify = True
                continue

            curr_costs = cost.split()
            curr_price = []
            for c in curr_costs:
                if isprice(c):
                    curr_price.append(c)

            if len(curr_price) == 0:
                if store == Migros:
                    verify = True
                    continue
                else:
                    prices.append(cost)
            elif len(curr_price) > 1:
                raise ValueError('Too much prices')
            else:
                prices.append(curr_price[0])

    # Get the list of tuples from two lists and merge them by using zip().
    list_of_tuples = list(zip(products, prices))

    # Converting lists of tuples into pandas Dataframe.
    df = pd.DataFrame(list_of_tuples, columns=['Product', 'Price'])
    df.to_csv(path_csv_out)

    print('Generated ' + path_csv_out)


def run(path_text_out, path_csv_out, store, im=None):
    """

    :param path_text_out: path to the output text file
    :param path_csv_out: path to the output csv file
    :param store: store to which the receipt refers
    :param im: image

    """
    if im is not None:
        # The original image should be taken with scanbot without flash, shadows and with neutral background
        im = binarize_image(im, store)

        # It is possible to change the language of the receipt. If any language is specified, english is used as default.
        receipt_text = image_to_string(im, lang='ita')
        lines = receipt_text.split('\n')

        puntuaction = replace_multiple(string.punctuation, ['.', ','], '')

        generate_text(lines, path_text_out, puntuaction, store)

    generate_csv(path_csv_out, path_text_out, store)


def main(args, csv_out_dir, txt_out_dir):
    """

    :param args: command line arguments
    :param csv_out_dir:
    :param txt_out_dir:
    """

    if args.store == 'migros':
        store = Migros
    elif args.store == 'lidl':
        store = Lidl
    else:
        raise ValueError('Invalid or missing store')

    if args.image is not None:
        # Open the input image and detect to which store the receipt refers to.
        # WIP: actually, only Migros and Lidl are detected.
        im = Image.open(args.image).convert('L')

        extension = ('.jpg', '.JPG', '.png', '.PNG')
        receipt_name = Path(args.image).name

        path_text_out = os.path.join(txt_out_dir, replace_multiple(receipt_name, extension, '.txt'))
        path_csv_out = os.path.join(csv_out_dir, replace_multiple(receipt_name, extension, '.csv'))

        run(path_text_out, path_csv_out, store, im)

    elif args.txt is not None:
        receipt_name = Path(args.txt).stem

        path_text_out = args.txt
        path_csv_out = os.path.join(csv_out_dir, '%s.csv' % receipt_name)

        run(path_text_out, path_csv_out, store)
    else:
        raise ValueError('Invalid or missing input')

    subprocess.call(['open', path_csv_out])


if __name__ == "__main__":
    args = parse_args()

    # Create the directories for the output file, if do not exist.
    csv_out_dir = 'out/csv/'
    txt_out_dir = 'out/txt/'

    check_dir(csv_out_dir)
    check_dir(txt_out_dir)

    main(args, csv_out_dir, txt_out_dir)
