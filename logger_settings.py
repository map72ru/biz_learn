from config import log_path
import datetime
import logging


current_date = str(datetime.datetime.now().date())
logging.basicConfig(filename=log_path+current_date+'.log', filemode='a', format='%(asctime)s - %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)
log = logging.getLogger('ml_borehole_cuttings')
