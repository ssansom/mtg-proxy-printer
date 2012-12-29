# -*- coding: utf-8 -*-
"""
Input csv format: Amount Name
10 Swamp
1 Mountain of Doom

Images in images/Mountain of Doom.jpg

Write decks in UTF-8 to manage cards like Æther Vial
"""

import sys, math, os, re, urllib, codecs

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
import settings_default as settings

def mtg_proxy_print(input_filename):
    input_fullpath = os.path.join(settings.DECKS_FULL_PATH, input_filename)
    if not os.path.exists(input_fullpath):
        raise Exception, 'File with the name "%s" doesn\'t exist.' % input_fullpath
    
    deck = read_deck(input_fullpath)
    download_missing_images(deck, settings.IMAGES_FULL_PATH)
    print_pdf(deck, input_filename)

def read_deck(input_fullpath):
    f = codecs.open(input_fullpath, "r", "utf-8" )
    #parse file into deck list
    deck = []
    for line in f:
        #remove BOM if present and strip
        line = line.lstrip(unicode(codecs.BOM_UTF8, "utf8" )).strip()
        match = re.match('(\d+) ([ \S]+)', line)
        if match is None:
            continue
        amount = int(match.group(1))
        name = match.group(2).strip()
        deck.extend([name] * amount)
    f.close()
    return deck

def get_image_full_path(card_name, images_full_path):
    return os.path.join(images_full_path, '%s.jpg' % card_name.replace("'",""))

def search_for_card(card_name):
    query_url = 'http://magiccards.info/query?q=%s' % (urllib.quote(card_name))
    print query_url
    page = urllib.urlopen(query_url)
    content = unicode(page.read(), "utf-8")
    page.close()
    search = u'<title>%s' % card_name
    if content.find(search) is -1:
        search = u'<title>%s' % card_name.replace("'","&#39;")
        if content.find(search) is -1:
          print 'Page title %s not found on %s' % (card_name, query_url)
          return False
    return content

def download_image(card_name, images_full_path):
    content = search_for_card(card_name)
    if not content:
        return False
    match = re.match('(.+)src="http://([a-z0-9\./]+)"\s+alt="%s"(.+)' % (card_name), content.replace("\n", ""))
    if match is None:
        print 'Image for %s not found.' % card_name
        return False
    img_url = 'http://%s' % match.group(2)
    new_url = get_image_full_path(card_name, images_full_path)
    urllib.urlretrieve(img_url, new_url.replace("'",""))
    if not os.path.exists(new_url):
        print 'WARNING: download of %s from %s not successful!' % (new_url, img_url)
        return False
    print 'Downloaded image from %s to %s' % (img_url, new_url)


def download_missing_images(deck, images_full_path):
    #download missing images
    for card_name in set(deck):
        path = get_image_full_path(card_name, images_full_path)
        if not os.path.exists(path):
            download_image(card_name, images_full_path)



def print_pdf(deck, input_filename):
    #card size in mm
    CARD_WIDTH = settings.CARD_WIDTH
    CARD_HEIGHT = settings.CARD_HEIGHT
    CARD_HORIZONTAL_SPACING = settings.CARD_HORIZONTAL_SPACING
    CARD_VERTICAL_SPACING = settings.CARD_VERTICAL_SPACING
    
    
    padding_left = (LETTER[0] - 3*(CARD_WIDTH+(2*CARD_HORIZONTAL_SPACING))*mm) / 2
    padding_bottom = (LETTER[1] - 3*(CARD_HEIGHT+(2*CARD_VERTICAL_SPACING))*mm) / 2
#    padding_left = (A4[0] - 3*CARD_WIDTH*mm) / 2
#    padding_bottom = (A4[1] - 3*CARD_HEIGHT*mm) / 2


    def make_page(cards, canvas):
        canvas.translate(padding_left, padding_bottom)
        col, row = 0, 3
        for card_name in cards:
            image = get_image_full_path(card_name, settings.IMAGES_FULL_PATH)
            if col % 3 == 0:
                row -= 1
                col = 0
            #x and y define the lower left corner of the image you wish to
            #draw (or of its bounding box, if using preserveAspectRation below).            
            canvas.drawImage(image, x=(col*CARD_WIDTH+((2*col)*CARD_HORIZONTAL_SPACING))*mm, y=(row*CARD_HEIGHT+((2*row-2)*CARD_VERTICAL_SPACING))*mm, width=CARD_WIDTH*mm, height=CARD_HEIGHT*mm)
            col += 1
        canvas.showPage()

    output_filename = '%s_print.pdf' % input_filename[:-4]
    output_fullpath = os.path.join(settings.OUTPUT_PATH, output_filename)
    canvas = Canvas(output_fullpath, pagesize=LETTER)

    CARDS_ON_PAGE = 9
    def number_of_pages(deck):
        return int(math.ceil(1.0 * len(deck) / CARDS_ON_PAGE))

    for index in range(number_of_pages(deck)):
        cards = deck[(index * CARDS_ON_PAGE):(index * CARDS_ON_PAGE + CARDS_ON_PAGE)]
        canvas.setFillColor(settings.PAGE_FILL_COLOR)
        canvas.rect(x=0,y=0,width=215*mm,height=279*mm,fill=True)
        make_page(cards, canvas)
    try:
        canvas.save()
    except IOError:
        print 'Save of the file %s failed. If you have the PDF file opened, close it.' % output_filename
        sys.exit(1)

    print '%s saved.' % output_filename
    
    #sheet for pack quick overview
    
    output_filename = '%s_overview.pdf' % input_filename[:-4]
    output_fullpath = os.path.join(settings.OUTPUT_PATH, output_filename)
    canvas = Canvas(output_fullpath, pagesize=LETTER)
    canvas.translate(padding_left, padding_bottom)

    #making list unique but maintain the order
    cards = list(set(deck))
    cards.sort(cmp=lambda x,y: cmp(deck.index(x), deck.index(y))) 
    
    multiplicator = int(math.ceil(math.sqrt(len(cards))))
    
    CARD_WIDTH = 3.0 * CARD_WIDTH / multiplicator
    CARD_HEIGHT = 3.0 * CARD_HEIGHT / multiplicator
    
    x, y = 0, multiplicator
    for card_name in cards:
        image = get_image_full_path(card_name, settings.IMAGES_FULL_PATH)
        if x % multiplicator == 0:
            y -= 1
            x = 0
        #x and y define the lower left corner of the image you wish to
        #draw (or of its bounding box, if using preserveAspectRation below).
        canvas.drawImage(image, 
                         x=x*CARD_WIDTH*mm, 
                         y=y*CARD_HEIGHT*mm, 
                         width=CARD_WIDTH*mm, 
                         height=CARD_HEIGHT*mm)
        canvas.setFillColorRGB(1,1,1)
        canvas.rect(x=x*CARD_WIDTH*mm + CARD_WIDTH*mm/10, 
                    y=y*CARD_HEIGHT*mm + CARD_HEIGHT*mm/1.5, 
                    width=CARD_WIDTH*mm/4, 
                    height=CARD_HEIGHT*mm/6, 
                    stroke=1, fill=1)
        canvas.setFillColorRGB(0,0,0)
        canvas.drawString(x=x*CARD_WIDTH*mm + CARD_WIDTH*mm/10 + CARD_WIDTH*mm/20, 
                          y=y*CARD_HEIGHT*mm + CARD_HEIGHT*mm/1.5 + CARD_HEIGHT*mm/20,
                          text="%dx" % deck.count(card_name))
        x += 1
    canvas.showPage()

    try:
        canvas.save()
    except IOError:
        print 'Save of the file %s failed. If you have the PDF file opened, close it.' % output_filename
        sys.exit(1)

    print '%s saved.' % output_filename

