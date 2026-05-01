import os
import yfinance as yf
import pandas as pd
import requests

LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 銘柄名辞書
NAMES = {
    "7011": "三菱重工",
    "4828": "ビジネスエンジニアリング",
    "8316": "三井住友FG",
    "8306": "三菱UFJ",
    "8331": "千葉銀行",
    "4063": "信越化学",
    "6981": "村田製作所",
    "1605": "INPEX",
    "6269": "三井海洋開発",
    "1963": "日揮HD",
    "8591": "オリックス",
    "3003": "ヒューリック",
    "8001": "伊藤忠商事",
    "8058": "三菱商事",
    "9432": "NTT",
    "9433": "KDDI",
    "5802": "住友電工",
    "8267": "イオン",
    "4182": "三菱ケミカルG",
    "1540": "純金ETF",
    "2638": "GXロボティックス&AI ETF",
    "8593": "三菱HCキャピタル",
    "4894": "クオリプス",
    "4369": "トリケミカル",
    "485A": "パワーエックス"
}

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
    df = ticker.history(period="30d")
    df = df.dropna()
    return df

def load_market_indices():
    tickers = {
        "日経平均": "^N225",
        "TOPIX": "^TOPX",
        "USDJPY": "JPY=X",
        "米10年金利": "^TNX",
        "VIX": "^VIX"
    }

    results = {}
    for name, symbol in tickers.items():
        try:
            df = yf.Ticker(symbol).history(period="2d")
            if len(df) >= 2:
                close = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]
                change = (close - prev) / prev * 100
                results[name] = f"{close:.2f} ({change:+.2f}%)"
            else:
                results[name] = "N/A"
        except:
            results[name] = "N/A"

    return results

def reversed_signal_with_score(df):
    if len(df) < 20:
        return 0, {}

    reasons = {}

    # 1. 3日連続下落
    cond1 = all(df["Close"].iloc[-i] < df["Close"].iloc[-i-1] for i in range(1,4))
    reasons["3日連続下落"] = cond1

    # 2. 当日反転
    cond2 = df["Open"].iloc[-1] < df["Close"].iloc[-1]
    reasons["当日反転"] = cond2

    # 3. 前日終値ブレイク
    cond3 = df["Close"].iloc[-1] > df["Close"].iloc[-2]
    reasons["前日終値ブレイク"] = cond3

    # 4. 出来高 +20%
    cond4 = df["Volume"].iloc[-1] > df["Volume"].iloc[-2] * 1.2
    reasons["出来高 +20%"] = cond4

    # 5. 5MA 上抜け
    ma5 = df["Close"].rolling(5).mean()
    cond5 = df["Close"].iloc[-1] > ma5.iloc[-1]
    reasons["5MA 上抜け"] = cond5

    # 6. RSI 50 上抜け
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    cond6 = rsi.iloc[-2] < 50 and rsi.iloc[-1] > 50
    reasons["RSI 50 上抜け"] = cond6

    # 7. MACD ゴールデンクロス
    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    cond7 = macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]
    reasons["MACD ゴールデンクロス"] = cond7

    score = (
        cond1 * 20 +
        cond2 * 20 +
        cond3 * 15 +
        cond4 * 15 +
        cond5 * 10 +
        cond6 * 10 +
        cond7 * 10
    )

    return score, reasons

def main():
    from datetime import datetime

    codes = [
        "7011","4828","8316","8306","8331",
        "4063","6981","1605","6269","1963",
        "8591","3003","8001","8058","9432",
        "9433","5802","8267","4182","1540",
        "2638","8593","4894","4369","485A"
    ]

    messages = []

    for code in codes:
        df = load_price(code)
        if df is None or df.empty:
            continue

        score, reasons = reversed_signal_with_score(df)

        if score >= 60:
            name = NAMES.get(code, "")
            msg = f"【{code} {name}】\nスコア：{score}\n"
            for k, v in reasons.items():
                mark = "✓" if v else "✗"
                msg += f"{mark} {k}\n"
            messages.append(msg)

    indices = load_market_indices()

    # ★ 日付を追加
    today = datetime.now().strftime("%Y-%m-%d")

    if messages:
        final_msg = "🔥反転初動シグナル🔥\n\n" + "\n".join(messages)
    else:
        final_msg = "本日の反転初動シグナル：該当なし\n\n【指数】\n"
        for k, v in indices.items():
            final_msg += f"{k}: {v}\n"

    # ★ メッセージ先頭に日付を付与
    final_msg = f"📅 {today}\n\n" + final_msg

    send_line(final_msg)


if __name__ == "__main__":
    main()
