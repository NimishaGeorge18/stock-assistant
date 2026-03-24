import mss
import mss.tools
from PIL import Image
import os
from datetime import datetime

STOCKS = {
    "ITC": {"top": 289, "left": 834, "width": 581, "height": 208},
    "RELIANCE": {"top": 289, "left": 834, "width": 581, "height": 208},
    "ONGC": {"top": 289, "left": 834, "width": 581, "height": 208},
}

os.makedirs("screenshots", exist_ok=True)

def take_screenshot(stock_name: str) -> str:
    region = STOCKS[stock_name]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/{stock_name}_{timestamp}.png"

    with mss.mss() as sct:
        screenshot = sct.grab(region)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)

    # resize to save Claude API cost
    img = Image.open(filename)
    img = img.resize((800, 500))
    img.save(filename)

    print(f"Screenshot saved: {filename}")
    return filename

def take_all_screenshots() -> dict:
    results = {}
    for stock in STOCKS:
        results[stock] = take_screenshot(stock)
    return results

if __name__ == "__main__":
    take_all_screenshots()