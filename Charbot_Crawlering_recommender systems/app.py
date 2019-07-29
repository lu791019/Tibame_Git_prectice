import random
import configparser
from flask import Flask, request, abort
import pandas as pd
from jieba.analyse import extract_tags,set_stop_words
from jieba import cut, set_dictionary, load_userdict,lcut

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
app = Flask(__name__)

#Token跟Secret從config.ini文件裡面改,以下勿動
config = configparser.ConfigParser()
config.read("config.ini")
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

#讀取爬網的資料,讀取結巴的字典跟stopword
df = pd.read_csv("jiankang_final.csv", encoding="utf-8")
set_dictionary("dict.txt.big")
set_stop_words("stopword.txt")

#line驗證的固定格式, 勿動
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'

#當使用者回傳TEXT時, 用def handle_message(event)函數
#使用者回傳的text是event.message.text
#回傳給line使用者,要用: line_bot_api.reply_message(event.reply_token,TextSendMessage(text='要回傳的文字'))
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #這個print不知道幹嘛, 反正留著
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    #設定使用者回傳的text 為ask
    ask=event.message.text
    #把ask用結巴取關鍵字
    list=extract_tags(ask)
    #把sk有"吃"這個字就增加'飲食'
    if "吃" in ask:
        list.append("飲食")
    #沒有取到關鍵字時
    if len(list) <= 0 :
        nothing="文字沒有被辨識到哦, 請換個方式問問看"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=nothing))
        return 0
    else:
        #設置limit:
        #如果ask的關鍵字有2個以下, 文章要符合全部關鍵字
        #如果ask的關鍵字有2個以上, 文章只要符合其中一半的關鍵字即可
        if len(list) <= 2 :
            limit=len(list)
        elif len(list) > 2 :
            limit = len(list)/2
        #content=要回復給使用者的內容
        content = ""

        y = 0
        for k in range(len(df)):
            #看符合多少個ask的關鍵字
            x = 0
            for l in list:
                if l in df["keywords"][k]:
                    x += 1
            #只推薦5則,太多會有bug
            if y>5:
                break
            #大於limit的文章, 加入content
            if x >= limit:
                # print(df["title"][k],df["網址"][k])
                content += '{}\n{}\n\n'.format(df["title"][k],df["網址"][k])
                y = y + 1
        #如果content為空
        if content == "":
            nothing = "文字沒有被辨識到哦, 請換個方式問問看"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=nothing))
        #把content回傳給使用者
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0


#當使用者傳圖貼時, 隨機回復(copy別人的~)
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("package_id:", event.message.package_id)
    print("sticker_id:", event.message.sticker_id)
    # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    print(index_id)
    sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id=sticker_id
    )
    line_bot_api.reply_message(
        event.reply_token,
        sticker_message)


if __name__ == '__main__':
    app.run()
