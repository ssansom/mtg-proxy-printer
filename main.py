import os
import sys

if __name__ == '__main__':
    try:
        import settings
    except ImportError:
        print 'You can modify settings by putting your definitions to settings.py file - just copy settings_default.py to settings.py and edit content'
        import settings_default as settings
    
    try:
        import reportlab
    except ImportError:
        print 'ReportLab not installed. Go to http://www.reportlab.org/'
        sys.exit(1)
        
    try:
        input_filename = os.path.basename(sys.argv[1])
    except IndexError:
        print 'Missing parameter! First parameter needs to be the txt filename in format deckname.txt'
        print 'Example: mtg_proxy_printer.py goblin.txt'
        sys.exit(1)
    
    from mtg_proxy_printer import mtg_proxy_print
    try:
        mtg_proxy_print(input_filename)
        print 'My work is done.'
    except Exception, msg:
        print msg
