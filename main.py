from flask import Flask, request
import requests
import logging
import re
from datetime import datetime
import time
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 你的 go-cqhttp 地址
CQHTTP_URL = "http://127.0.0.1:8003"

# 存储待验证的入群请求
join_requests = {}

# 发送群聊消息的函数
def send_group_message(group_id, message):
    url = f"{CQHTTP_URL}/send_group_msg"
    data = {
        'group_id': group_id,
        'message': message
    }
    response = requests.post(url, json=data)
    logging.debug(f"Send group message response: {response.text}")

def eac_stat(Player_name):
    response1 = requests.get(f"https://api.bfeac.com/case/EAID/{Player_name}")
    bfeac_stat = response1.json()
    return bfeac_stat

def ban_stat(Player_personid):
    response2 = requests.get(f"https://api.bfban.com/api/player?personaId={Player_personid}")
    bfban_stat = response2.json()
    return bfban_stat

def handle_message(event):
    data = request.json
    user_id = event['user_id']
    message_id = event['message_id']
    group_id = data['group_id']
    message = data.get('message')
    raw_message = data.get('raw_message')
    if message.startswith('/ping'):
        return send_group_message(group_id,'PONG!')
    
# 处理群成员增加事件，验证备注并处理入群请求
def handle_group_increase(event):
    user_id = event['user_id']
    group_id = event['group_id']
    comment = event.get('comment', '')  # 获取用户的申请备注，默认空字符串
    request_flag = event['flag']
    join_requests[group_id] = {'flag': request_flag, 'user_id': user_id, 'group_id': group_id} # 存储该群的加入请求信息
    match = re.search(r'答案：(\S+)', comment)
    if match:
        answer = match.group(1)
    if comment == '正确答案！！！！':
        send_group_message(group_id,"文字")
        time.sleep(3)
        set_group_card(group_id,user_id,answer)   #修改群昵称
        time.sleep(2)                     #别改太快不然容易被查出来
        send_group_message(group_id,f'[CQ:at,qq={user_id}] 欢迎入群\n机器人已经修改你的群昵称为: {answer}')
        del join_requests[group_id]  # 移除已处理的请求

#修改群昵称！
def set_group_card(group_id,user_id,card):
    url = f"{CQHTTP_URL}/set_group_card"
    data = {
        'group_id': group_id,
        'user_id': user_id,
        'card': card
    }
    response = requests.post(url, json=data)
    logging.debug(f"Approve request response: {response.text}")    

# 批准入群请求
def approve_group_request(flag):
    url = f"{CQHTTP_URL}/set_group_add_request"
    data = {
        'flag': flag,
        'sub_type': 'add',
        'approve': True
    }
    response = requests.post(url, json=data)
    logging.debug(f"Approve request response: {response.text}")

"""# 拒绝入群请求
def reject_group_request(flag):
    url = f"{CQHTTP_URL}/set_group_add_request"
    data = {
        'flag': flag,
        'sub_type': 'add',
        'approve': False,
        'reason': '备注信息不正确，管理员拒绝了您的申请'  # 可选理由 只在拒绝时有用！
    }
    response = requests.post(url, json=data)
    logging.debug(f"Reject request response: {response.text}")"""

# 定义接收事件的路由
@app.route('/callback/', methods=['POST'])
def callback():
    logging.debug(f"Received request: {request.json}")
    event = request.json
    if event['post_type'] == 'request':
        if event['sub_type'] == 'add':
            handle_group_increase(event)
    elif event['post_type'] == 'message':
        handle_message(event)

    return 'OK'

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(port=8083)
