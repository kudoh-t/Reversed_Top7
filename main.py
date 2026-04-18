import os
import yfinance as yf
import pandas as pd
import requests
import datetime as dt

LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

def load_price(code):
    ticker = yf.Ticker(f"{code}.T")
    df = ticker.history(period="20d")
    df = df.dropna()
    return df

def reversed_signal(df):
    # 1. 3日連続下落
    cond1 = all(df["Close"].iloc[-i] < df["Close"].iloc[-i-1] for i in range(1,4))

    # 2. 当日反転（始値 < 現在値）
    cond2 = df["Open"].iloc[-1] < df["Close"].iloc[-1]

    # 3. 前日終値ブレイク
    cond3 = df["Close"].iloc[-1] > df["Close"].iloc[-2]

    # 4. 出来高 +20%
    cond4 = df["Volume"].iloc[-1] > df["Volume"].iloc[-2] * 1.2

    # 5. 5MA 上抜け
    ma5 = df["Close"].rolling(5).mean()
    cond5 = df["Close"].iloc[-1] > ma5.iloc[-1]

    # 6. RSI 30〜50 → 上抜け
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    cond6 = rsi.iloc[-2] < 50 and rsi.iloc[-1] > 50

    # 7. MACD ゴールデンクロス
    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    cond7 = macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]

    return all([cond1, cond2, cond3, cond4, cond5, cond6, cond7])

def main():
    codes = ["7203", "6758", "9984", "8035", "6861", "4063", "4502"]  # ← ここに監視銘柄を追加

    hits = []
    for code in codes:
        df = load_price(code)
        if reversed_signal(df):
            hits.append(code)

    if hits:
        msg = "🔥反転初動シグナル検出🔥\n" + "\n".join(hits)
    else:
        msg = "本日の反転初動シグナル：該当なし"

    send_line(msg)

if __name__ == "__main__":
    main()
