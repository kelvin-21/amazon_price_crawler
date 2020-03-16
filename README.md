### Amazon Price Crawler

- Get the price and stock information of 70 products on Amazon.jp within 30 seconds
- Detect different web states and perform corresponding actions
- Bypass captcha in Amazon
- Prompt alert in Telegram if desired price appears
- Support multi-threading
- For Amazon.jp only

### Files

----
amazon_price.py

Need to input:
- `my_token = ''  # telegram bot token` Telegram bot token (Go to [here](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-channel-connect-telegram?view=azure-bot-service-4.0) for more info)
- ` user = ''  # telegram user chat id` Telegram user chat id (Go to [here](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id) for more info)
- `num_partition = 1  # number of thread` Number of threads (default=1)

----

product_list.csv

| product_code  | price | update_time| remark | alert_threshold | good_price | link |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| B07573632C  | 19490  | 2020-02-25_12:56:02 | normal | 1000 | 628 | * |
| B01545GQ9O  | 8900  | 2020-02-22_23:50:20 | normal | 1000 | 636 | * |
| ... | ... | ... | ... | ... | ... | ... |

- The **product_code** can be found on the web url on Amazon
- Define your desired purchase price at **alert_threshold**
- **remark** ,**good_price**, **link** are for your notes


Other required files:
- chrome driver for selenium (put it in this directory)
- tesseract.exe (put it in the path C:\Program Files\Tesseract-OCR\tesseract.exe)
