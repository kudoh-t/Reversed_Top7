from flask import Flask, request
import requests

# あなたのチャネルアクセストークン（長期）を貼る
LINE_TOKEN = "ここに貼る"

# あなたの userId を貼る（後で説明）
USER_ID = "ここに貼る"

app = Flask(__name__)

def send_line(message: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    requests.post(url, headers=headers, json=data)

@app.post("/webhook")
def webhook():
    data = request.json
    print("受信:", data)

    symbol = data.get("symbol", "N/A")
    price = data.get("price", "N/A")
    time = data.get("time", "N/A")

    message = f"【反転シグナル】\n銘柄: {symbol}\n価格: {price}\n時刻: {time}"
    send_line(message)

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
