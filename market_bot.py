import os
import logging
import yfinance as yf
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import matplotlib.pyplot as plt
import tempfile
import mplfinance as mpf

# Telegram Bot Token (hardcoded for your bot)
TELEGRAM_BOT_TOKEN = "8022974540:AAEOXDWCDtD8w55hU_y4MTOxSCc1H0T6mmo"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Supported commands for /help
COMMANDS = [
    "/price SYMBOL - Stock ka price",
    "/chart SYMBOL TIMEFRAME - Candlestick chart",
    "/fundamentals SYMBOL - Stock fundamentals",
    "/help - Saare commands ki list",
    "/language hindi - Hindi reply",
    "/language english - English reply",
]

# Language state (simple, per session)
LANGUAGE = "hindi"

# Helper: get price
def get_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        if data.empty:
            return "⚠️ Stock nahi mila. Symbol check karein."
        price = data['Close'].iloc[-1]
        return f"{symbol.upper()} ka price: ₹{price:.2f}"
    except Exception as e:
        logger.exception("Price fetch error")
        return f"⚠️ Price laane mein dikkat: {e}"

# Helper: get fundamentals
def get_fundamentals(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        pe = info.get("trailingPE", "N/A")
        eps = info.get("trailingEps", "N/A")
        cap = info.get("marketCap", "N/A")
        high = info.get("fiftyTwoWeekHigh", "N/A")
        low = info.get("fiftyTwoWeekLow", "N/A")
        return (f"{symbol.upper()} Fundamentals:\n"
                f"P/E: {pe}\nEPS: {eps}\nMarket Cap: {cap}\n52W High: {high}\n52W Low: {low}")
    except Exception as e:
        logger.exception("Fundamentals error")
        return f"⚠️ Data nahi mil paaya: {e}"

# Helper: plot chart
def get_chart(symbol, timeframe="1d"):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="7d" if timeframe=="1d" else timeframe)
        if data.empty:
            return None
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            mpf.plot(
                data,
                type='candle',
                style='charles',
                title=f"{symbol.upper()} {timeframe} Candlestick Chart",
                ylabel='Price',
                savefig=tmpfile.name
            )
            return tmpfile.name
    except Exception as e:
        logger.exception("Chart error")
        return None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/price", "/chart"], ["/fundamentals", "/help"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Swagat hai! Stock ka price, chart, ya fundamentals poochne ke liye command bhejein.",
        reply_markup=markup
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join(COMMANDS)
    await update.message.reply_text(f"🆘 Commands:\n{msg}")

# /language command
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LANGUAGE
    if len(context.args) == 0:
        await update.message.reply_text("/language hindi ya /language english likhein.")
        return
    lang = context.args[0].lower()
    if lang in ["hindi", "english"]:
        LANGUAGE = lang
        await update.message.reply_text(f"Language set: {lang}")
    else:
        await update.message.reply_text("Sirf hindi ya english support hai.")

# /price command
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /price SYMBOL (jaise RELIANCE.NS)")
        return
    symbol = context.args[0].upper()
    await update.message.reply_text(get_price(symbol))

# /fundamentals command
async def fundamentals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /fundamentals SYMBOL (jaise RELIANCE.NS)")
        return
    symbol = context.args[0].upper()
    await update.message.reply_text(get_fundamentals(symbol))

# /chart command
async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /chart SYMBOL [TIMEFRAME] (jaise RELIANCE.NS 1d)")
        return
    symbol = context.args[0].upper()
    timeframe = context.args[1] if len(context.args) > 1 else "1d"
    chart = get_chart(symbol, timeframe)
    if chart:
        with open(chart, 'rb') as f:
            await update.message.reply_photo(photo=f)
        os.remove(chart)
    else:
        await update.message.reply_text("⚠️ Chart banaane mein dikkat aayi.")

# Main function
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("fundamentals", fundamentals_command))
    app.add_handler(CommandHandler("chart", chart_command))
    print("✅ Bot LIVE! (Bot chal raha hai)")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import sys
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
