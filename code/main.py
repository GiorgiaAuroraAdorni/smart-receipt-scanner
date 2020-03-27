from PIL import Image
from pytesseract import image_to_string
import pandas as pd
import re
import string
from os import listdir
from os.path import isfile, join
import os


class Lidl(enumerate):
    begin = 'CHF'
    finish = 'Totale'


class Migros(enumerate):
    begin = 'CHF'
    finish = 'TOTALE'


def check_dir(directory):
    """
    :param directory: path to the directory
    """
    os.makedirs(directory, exist_ok=True)


def isfloat(value):
  """

  :param value:
  :return:
  """
  try:
    float(value)
    return True
  except ValueError:
    return False


def replaceMultiple(mainString, toBeReplaces, newString):
    """ Replace a set of multiple sub strings with a new string in main string. """

    # Iterate over the strings to be replaced
    for elem in toBeReplaces:
        # Check if string is in the main string
        if elem in mainString:
            # Replace the string
            mainString = mainString.replace(elem, newString)

    return mainString


def searchMultiple(mainString, toSearch):
    """ Replace a set of multiple sub strings with a new string in main string. """

    # Iterate over the strings to be replaced
    for elem in toSearch:
        # Check if string is in the main string
        if elem in mainString:
            # Replace the string
            return True

    return False


def binarize_image(path_to_image, store):
    """
    """
    im = Image.open(path_to_image).convert('L')

    if store == Lidl:
        for i in range(im.size[0]):
            for j in range(im.size[1]):
                if im.getpixel((i, j)) > 170:
                    im.putpixel((i, j), 255)
                else:
                    im.putpixel((i, j), 0)

    return im


def generate_text(b, begin, end, f, lines, path_text_out, puntuaction, start, store):
    """

    :param b:
    :param begin:
    :param end:
    :param f:
    :param lines:
    :param path_text_out:
    :param puntuaction:
    :param start:
    """
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
                if line.startswith(begin):
                    continue

                if store is Lidl:
                    if line[0].isdigit():
                        continue

                if searchMultiple(line, list(puntuaction)):
                    line = replaceMultiple(line, list(puntuaction), '')

                text_file.writelines(line)
                text_file.writelines('\n')

            if end:
                text_file.writelines(line)
                text_file.writelines('\n')
                break


def generate_csv(path_csv_out, path_text_out, store):
    """

    :param path_csv_out:
    :param path_text_out:
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
                    discount = float(replaceMultiple(line, [p, '\n'], '').split()[0])
                    total = round(float(price[-1].split()[0]), 2)
                    price[-1] = str(total - discount)
                    continue

            p = re.split(r'(\d+)', line)[0]
            if store is Lidl:
                if len(p) < 3:
                    continue

            product.append(p)
            cost = replaceMultiple(line, [p, '\n'], '')
            if isfloat(cost.split()[0]):
                price.append(cost.split()[0])
            else:
                price.append(cost.split()[1])
    # get the list of tuples from two lists.
    # and merge them by using zip().
    list_of_tuples = list(zip(product, price))

    # Converting lists of tuples into
    # pandas Dataframe.
    df = pd.DataFrame(list_of_tuples, columns=['Product', 'Price'])

    # Print data.
    df.to_csv(path_csv_out)


def main(path_to_image, path_text_out, path_csv_out, store):
    """

    :param path_to_image:
    :param path_text_out:
    :param path_csv_out:
    """

    # The original image should be taken with scanbot without flash, shadows and with neutral background
    im = binarize_image(path_to_image, store)

    receipt_text = image_to_string(im, lang='ita')
    lines = receipt_text.split('\n')

    b = re.compile(store.begin)
    f = re.compile(store.finish)
    start = False
    end = False

    puntuaction = replaceMultiple(string.punctuation, ['.', ','], '')

    generate_text(b, store.begin, end, f, lines, path_text_out, puntuaction, start, store)

    generate_csv(path_csv_out, path_text_out, store)


if __name__ == '__main__':

    images_dir = '../images/'
    csv_out_dir = 'out/csv/'
    txt_out_dir = 'out/txt/'
    check_dir(csv_out_dir)
    check_dir(txt_out_dir)

    images = [f for f in listdir(images_dir) if isfile(join(images_dir, f))]
    extension = ('.jpg', '.JPG', '.png', '.PNG')
    images = [f for f in images if f.endswith(extension)]

    for im in images:
        path_to_image = images_dir + im
        path_text_out = os.path.join(txt_out_dir, replaceMultiple(im, extension, '.txt'))
        path_csv_out = os.path.join(csv_out_dir, replaceMultiple(im, extension, '.csv'))

        if re.search('lidl', path_to_image):
            try:
                main(path_to_image, path_text_out, path_csv_out, Lidl)
                print('Generated ' + path_csv_out)
            except:
                print('Retake the photo ' + path_to_image)
        elif re.search('migros', path_to_image):
            try:
                main(path_to_image, path_text_out, path_csv_out, Migros)
                print('Generated ' + path_csv_out)
            except:
                print('Retake the photo ' + path_to_image)
