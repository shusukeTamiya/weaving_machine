import cv2
import time

from smtplib import SMTP

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email.utils import formatdate
import ssl
from smtplib import SMTP_SSL
from datetime import datetime


class LimitedList:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.data = []

    def append(self, value):
        if len(self.data) >= self.max_size:
            self.data.pop(0)  # 一番古いデータを削除
        self.data.append(value)

    def count(self, value):
        return self.data.count(value)


    def __repr__(self):
        return repr(self.data)
    
def createMIMEText(sender, receiver, message, subject):
    msg = MIMEText(message, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg['Date'] = formatdate()
    return msg

def send_email(msg):
    account = "tomaty324@gmail.com"
    password = "cbom muwj esur auhr"

    host = "smtp.gmail.com"
    port = 465

    context = ssl.create_default_context()
    server = SMTP_SSL(host, port, context=context)

    server.login(account, password)

    server.send_message(msg)

    server.quit()

#### メールの設定 ####
sender = "tomaty324@gmail.com"

receiver = "tttamiya324@gmail.com"
#現在の時間を取得
now = datetime.now()
formatted_time = now.strftime("%Y年%m月%d日 %H時%M分")

subject = "機械が停止しました"
message = f"{formatted_time} に機械が停止しました"
mime = createMIMEText(sender, receiver, message, subject)


#### 動作検知 ####
movie = cv2.VideoCapture('/home/tamiya/Videos/weave_machine_demo1.MOV')

red = (0, 0, 255) # 枠線の色
before = None # 前回の画像を保存する変数
fps = int(movie.get(cv2.CAP_PROP_FPS)) #動画のFPSを取得
before_flag = None
flag = None

limited_list = LimitedList(max_size=120)

    


while True:
    # 画像を取得
    ret, frame = movie.read()
    # 再生が終了したらループを抜ける
    if ret == False: break
    # 白黒画像に変換
    frame2 = cv2.resize(frame, dsize=None, fx=0.25, fy=0.25)
    gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    if before is None:
        before = gray.astype("float")
        continue
    #現在のフレームと移動平均との差を計算
    cv2.accumulateWeighted(gray, before, 0.97)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(before))
    #frameDeltaの画像を２値化
    thresh = cv2.threshold(frameDelta, 3, 255, cv2.THRESH_BINARY)[1]
    #輪郭のデータを得る
    contours = cv2.findContours(thresh,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)[0]
    

    if limited_list.count(0) >= 80:
        flag = 0
        if before_flag == 1:
            print("メールを送信します")
            send_email(mime)
    else:
        flag = 1
    
    before_flag = flag
    if len(contours) == 0:
        limited_list.append(0)
    else:
        limited_list.append(1)

    # 差分があった点を画面に描く
    for target in contours:
        x, y, w, h = cv2.boundingRect(target)
        if w < 10: continue # 小さな変更点は無視
        cv2.rectangle(frame2, (x, y), (x+w, y+h), red, 2)
    

    #ウィンドウでの再生速度を元動画と合わせる
    time.sleep(1/fps)
    # ウィンドウで表示
    cv2.imshow('target_frame', frame2)
    # Enterキーが押されたらループを抜ける
    if cv2.waitKey(1) == 13: break

cv2.destroyAllWindows() # ウィンドウを破棄
