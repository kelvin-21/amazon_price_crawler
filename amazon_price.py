from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import pandas as pd
import requests
import urllib.request
import random
import time
from enum import Enum
from PIL import Image
import pytesseract
import threading
import math
import warnings
warnings.filterwarnings("ignore")

my_token = ''  # telegram bot token
user = ''  # telegram user chat id


class State(Enum):
    PRICE_EXIST = 'price_exists'
    OUT_OF_STOCK = 'out_of_stock'
    PAGE_DNE = 'page_does_not_exist'
    CAPTCHA = 'captcha'
    CAPTCHA_REFRESH = 'captcha_refresh' # failed in solving captcha
    UNKNOWN_ERROR = 'unknown_error'


class Amazon():
    
    def __init__(self, method=1):
        self.state = None
        self.products = pd.read_csv('product_list.csv')
        self.proxy_list = None
        self.PROXY = None
        self.driver = None
        self.method = method
        
        # data received when getting state
        self.new_price_str = None
        self.captcha_url = None
        self.captcha_text = None
        self.i = 0
        self.product_price = -1
        self.deliver_fee = -1
        self.element = None
        self.type_element = None
        self.click_element = None
        
        print('[METHOD] Use method {} for get_web_state'.format(self.method))
        
    def initialize(self):
        self.new_price_str = None
        self.captcha_url = None
        self.captcha_text = None
        self.state = None
        self.i = 0
        self.product_price = -1
        self.deliver_fee = -1
        self.element = None
        self.type_element = None
        self.click_element = None
        
    def launch_driver(self, use_headless=False, disable_img=False):
        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"
        chrome_options = webdriver.chrome.options.Options()
        if use_headless:
            chrome_options.add_argument("--headless")
            print('[DRIVER] Use headless mode')
        if disable_img:
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            print('[DRIVER] Disable images')
        self.driver = webdriver.Chrome(desired_capabilities=capa, options=chrome_options)
        print('[DRIVER] Driver launched')
        
    def driver_get_web(self):
        url = 'https://www.amazon.co.jp/gp/offer-listing/' + self.products['product_code'].iloc[self.i]
        self.driver.get(url)
        
# -------------------- Strategy -------------------- #
        
    def get_web_state(self, method=1):
        if method == 1:
            self.get_web_state_method_1()
            
    def action(self):
        if self.state == State.PRICE_EXIST:
            self.action_PRICE_EXIST()
        elif self.state == State.OUT_OF_STOCK:
            self.action_OUT_OF_STOCK()
        elif self.state == State.CAPTCHA:
            self.action_CAPTCHA()
        elif self.state == State.CAPTCHA_REFRESH:
            self.action_CAPTCHA_REFRESH()
        elif self.state == State.PAGE_DNE:
            self.action_PAGE_DNE()
        elif self.state == State.UNKNOWN_ERROR:
            self.action_UNKNOWN_ERROR()
        self.initialize()
        
# -------------------- Strategy End -------------------- #
        
    def action_PRICE_EXIST(self):
        new_price = self.element_str_to_price()
        self.update_price(new_price)
        self.check_alert()
        print('[{}] {} ￥{} ({} + {}) ({})'.format(
            self.i, self.products['product_code'].iloc[self.i], new_price, self.product_price, self.deliver_fee, self.get_time_now()))
    
    def action_OUT_OF_STOCK(self):
        print('[{}] {} Out of stock ({})'.format(
            self.i, self.products['product_code'].iloc[self.i], self.get_time_now()))
    
    def action_CAPTCHA(self):
        self.type_element = self.driver.find_element_by_xpath('//*[@id="captchacharacters"]')
        self.click_element = self.driver.find_element_by_xpath('/html/body/div/div[1]/div[3]/div/div/form/div[2]/div/span/span/button')
        self.send_keys_human(self.type_element, self.captcha_text)
        time.sleep(random.uniform(0.5, 1))
        self.click_element.click()
        time.sleep(2)
        # go back to where we got stopped, i is the same i
        self.get_web_state()
        self.action()
    
    def action_CAPTCHA_REFRESH(self):
        self.click_element = self.driver.find_element_by_xpath('/html/body/div/div[1]/div[3]/div/div/form/div[1]/div/div/div[2]/div/div[2]/a')
        time.sleep(1)
        self.click_element.click()
        time.sleep(1)
    
    def action_PAGE_DNE(self):
        print('[{}] {} Page does not exist ({})'.format(
            self.i, self.products['product_code'].iloc[self.i], self.get_time_now()))
    
    def action_UNKNOWN_ERROR(self):
        print('[{}] {} Unknown Error ({})'.format(
            self.i, self.products['product_code'].iloc[self.i], self.get_time_now()))
        
    def get_web_state_method_1(self):
        
        for j in range(0, 10):
            
            # id (olpOfferList)
            try:
                self.element = WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.ID, 'olpOfferList')))
                self.element = WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.ID, 'olpOfferList')))
                self.driver.execute_script("window.stop();")
                self.new_price_str = self.element.text
                if '￥' in self.element.text:
                    self.state = State.PRICE_EXIST
                else:
                    self.state = State.OUT_OF_STOCK
                return
            except:
                pass
            
            # page does not exist
            try:
                if str(self.driver.current_url) == 'https://www.amazon.co.jp/gp/errors/404.html':
                    self.driver.execute_script("window.stop();")
                    self.state = State.PAGE_DNE
                    return
            except:
                pass
            
            # id (captchacharacters)
            try:
                self.element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.ID, 'captchacharacters')))
                self.element = WebDriverWait(self.driver, 0.1).until(EC.presence_of_element_located((By.ID, 'captchacharacters')))
                self.driver.execute_script("window.stop();")
                self.state = State.CAPTCHA
                images = self.driver.find_elements_by_tag_name('img')
                for image in images:
                    if 'https://images-na.ssl-images-amazon.com/captcha' in image.get_attribute('src'):
                        self.captcha_url = image.get_attribute('src')
                        print('[CAPTCHA] captcha, now solving... captcha_url = %s' % self.captcha_url)
                self.captcha_text = self.captcha_solver()
                return
            except:
                pass
        
        
        self.state = State.UNKNOWN_ERROR

    def get_time_now(self, for_file_name=False):
        if for_file_name:
            return datetime.now().strftime('%Y-%m-%d_%H%M%S')
        else:
            return datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        
    def chunks(self, my_list, n):
        """Yield successive n-sized chunks from lst."""
        lists = []
        for i in range(0, len(my_list), n):
            lists.append(my_list[i:i + n])
        return lists
    
    def partition_list(self, num_partition):
        l = list(range(0, len(self.products)))
        lists = self.chunks(l, math.ceil(len(self.products)/num_partition))
        return lists
        
    def element_str_to_price(self):
        text = self.new_price_str
        s_i = None  # section index
        yen_index = None  # first index that contains '￥'
        deliver_fee_index = None
        price = ''
        deliver_fee = ''
        
        sections = [i for i, ltr in enumerate(text) if ltr == '新']
        sections = [0] + sections + [len(text)]
        for i in range(0, len(sections)-1):
            if '￥' in text[sections[i]:sections[i+1]]:
                s_i = i
                yen_index = text[sections[i]:sections[i+1]].find('￥')
                break
        
        if yen_index is None:  # cannot find '￥'
            self.state == State.OUT_OF_STOCK
            return
        
        price = text[yen_index:yen_index+8]  # 8 is hard coded
        price = ''.join(c for c in price if c.isdigit())
        
        if '送料(現段階では不明)' in text[sections[s_i]:sections[s_i+1]]:
            deliver_fee = '99999'
        elif '（配送料）' in text[sections[s_i]:sections[s_i+1]]:  # then we have deliver fee
            deliver_fee_index = text[sections[s_i]:sections[s_i+1]].find('配送料）')
            deliver_fee = text[deliver_fee_index-9:deliver_fee_index]  # 9 is hard coded
            deliver_fee = ''.join(c for c in deliver_fee if c.isdigit())
        else:
            deliver_fee = '0'
        
        self.product_price = int(price)
        self.deliver_fee = int(deliver_fee)
        total = self.product_price + self.deliver_fee
        return total
        
    def update_price(self, new_price):
        self.products.at[self.i, 'price'] = new_price
        self.products.at[self.i, 'update_time'] = str(self.get_time_now())
        
    def tg_msg(self, bot_message, user_chat_id):
        bot_token = my_token
        bot_chatID = user_chat_id
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
        return response.json()

    def check_alert(self):
        if self.products['price'].iloc[self.i] <= self.products['alert_threshold'].iloc[self.i]:
            offer_listing_url = 'https://www.amazon.co.jp/gp/offer-listing/' + self.products['product_code'].iloc[self.i]
            product_url = 'https://www.amazon.co.jp/gp/product/' + self.products['product_code'].iloc[self.i]
            msg = '---------- [ A L E R T ] ----------\n{} ￥{}\nProduct price = {}\nDeliver fee = {}\n{}\n{}'.format(
                self.products['product_code'].iloc[self.i], 
                self.products['price'].iloc[self.i],
                self.product_price,
                self.deliver_fee,
                offer_listing_url, 
                product_url)
            self.tg_msg(msg, user)
            print('\n%s\n' % msg)
            
    def captcha_solver(self):
        # url -> result string
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        img_data = requests.get(self.captcha_url).content
        file_name = 'captcha_img_%s.jfif' % self.get_time_now(for_file_name=True)
        with open(file_name, 'wb') as handler:
            handler.write(img_data)
            handler.close()
        text = pytesseract.image_to_string(Image.open(file_name))
        
        # if text contains more than 6 char, then fail.
        # if text contains something other than capital letter, then fail.
        
        text = text.replace(' ', '')
        if text is None:
            self.state = State.CAPTCHA_REFRESH  # failed
            return None
        elif len(text) != 6:
            self.state = State.CAPTCHA_REFRESH  # failed
        elif not text.isupper():
            self.state = State.CAPTCHA_REFRESH  # failed
        else:
            print('[CAPTCHA] text = {}'.format(text))
            self.captcha_text = text
            self.state = State.CAPTCHA  # can have a try
        return text
    
    def send_keys_human(self, element, text):
        for i in range(0, len(text)):
            element.send_keys(text[i])
            time.sleep(random.uniform(0.2, 0.5))
        
    def run(self, i_start=-1, i_end=-1):
        if i_start == -1:
            i_start = 0
        if i_end == -1:
            i_end = len(self.products)
        
        start = time.time()
        for i in range(i_start, i_end):
            self.i = i
            self.driver_get_web()
            self.get_web_state()
            self.action()
        self.products.to_csv('product_list.csv', index=False)
        end = time.time()
        minute, second = int((end-start)/60), int((end-start)%60)
        print('[FINISHED] time used = {} min {} sec'.format(minute, second))
        
        
def job(i_start=-1, i_end=-1):
    a = Amazon(method=1)
    if i_start == -1:
        i_start = 0
    if i_end == -1:
        i_end = len(a.products)
    a.launch_driver(use_headless=False, disable_img=False)
    while 1:
        a.run(i_start, i_end)


def job_multithread(num_partition=1):
    a = Amazon(method=1)
    lists = a.partition_list(num_partition)

    threads = []
    for i in range(0, len(lists)):
        i_start = lists[i][0]
        i_end = lists[i][-1]
        t = threading.Thread(target=job, args=(i_start, i_end,))
        threads.append(t)
        t.start()

    # will never reach here (?)
    for i in range(0, len(threads)):
        threads[i].join()

num_partition = 1  # number of thread
job_multithread(num_partition)