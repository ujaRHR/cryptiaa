from email import message
from urllib import response
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, Defaults, Updater, Dispatcher, CallbackContext
from pycoingecko import CoinGeckoAPI
from tabulate import tabulate
import json
from datetime import datetime
from numerize import numerize
import time
import requests
cg = CoinGeckoAPI()

apiKey = '5123114329:AAE6BMUem5V_VgxF6tMPgkAon8hGE5b9cNM'

## Reused Text
######################################
credit = f"\n\n✪<b> Bot by @dchklg </b>"
errorAlert = f'⚠️ Please provide a valid crypto name/symbol. Type /help to know more...'
######################################

def startCommand(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello <i>{update.message.from_user.first_name}</i> 👋 \nI am Cryptia, your crypto assistant. Get notified instantly when a crypto price goes above or below your target. \nType /help to know more...")

# Help Menu
def helpMenu(update, context):
    response = '📚 <b>Cryptia is a Telegram bot to check current crypto market. It will notify you when a crypto price goes above or below your target.</b>\n\n'
    response += '<b>/price name</b> - Check crypto price. \n'
    response += '<b>/alert name &gt;/&lt; price</b> - Set alert to get instant notification.\n'
    response += '<b>/top10</b> - Top 10 crypto by market cap. \n'
    response += '<b>/trending</b> - Trending Coins (7d) \n'
    response += '<b>/stats</b> - Global crypto stats. \n'
    response += '<b>/check name</b> - Check crypto details\n'
    response += '<b>/topx</b> - Check Top5 exchanger\n'
    response += '<b>/status</b> - Check API/Bot status\n'
    response += '<b>/help</b> - Show this message. \n'
    response += '<b>/example</b> - Show examples.'
    response += credit

    context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode=ParseMode.HTML)
    context.bot.pinChatMessage(chat_id=update.message.chat_id, message_id=(update.message.message_id)+1, disable_notification=False)


# Example Menu
def exampleMenu(update, context):
    response = '📚 <b> Some Command Example</b> 📚\n\n' 
    response += '📍<b>/price bitcoin</b> - <pre>Check Bitcoin price</pre>\n'
    response += '📍<b>/alert ltc &gt; 150</b> - <pre>Alert when LTC reaches $150</pre>\n'
    response += '📍<b>/top10</b> - <pre>Show top10 crypto (market cap)</pre>\n'
    response += '📍<b>/trending</b> - <pre>Show trending crypto</pre>\n'
    response += '📍<b>/stats</b> - <pre>Show global crypto stats</pre>\n'
    response += '📍<b>/check eth</b> - <pre>Check crypto details</pre>\n'
    response += '📍<b>/topx</b> - <pre>Top 5 exchanger</pre>\n'
    response += '📍<b>/status</b> - <pre>Check API/Bot status</pre>'
    response += credit

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

# Check current price
def currentPrice(update, context):
    if len(context.args) > 0:
        alter(context.args[0].lower())
        if alter.matched == "NO":
            response = errorAlert
            context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        else:
            price = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={alter.apiId}&vs_currencies=usd').text
            price = json.loads(price)
            
            response = f'📈 Current price of {alter.cryptoNameFinal} is <b>${float(price[alter.apiId]["usd"])}</b>''\n\n'
            response += f'🌐 Get Price, Chart, and Info:\n'
            response += f'<a href="https://coingecko.com/en/coins/{alter.apiId}">coingecko.com/en/coins/{alter.apiId}</a>\n'
            response += credit

            context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=response)

# Set price alert for specific crypto (multiple)
def priceAlert(update, context):
    if len(context.args) > 2:
        alter(context.args[0].lower())
        sign = context.args[1]
        price = context.args[2]

        context.job_queue.run_repeating(priceAlertCallback, interval=15, first=15, context=[alter.apiId, sign, price, update.message.chat_id])

        priceNow = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={alter.apiId}&vs_currencies=usd').text
        priceNow = json.loads(priceNow)

        response = f'⏰ I will send you a message when the price of {alter.cryptoNameFinal} reaches ${price} \n\n'
        response += f'📈 Current price of {alter.cryptoNameFinal} is <b>${float(priceNow[alter.apiId]["usd"])}</b>'
        response += credit
    else:
        response = '⚠️ Please provide a crypto code and a price value: \nExample: <b>/alert BTC > 40000</b>'

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def priceAlertCallback(context):
    crypto = context.job.context[0]
    sign = context.job.context[1]
    price = context.job.context[2]
    chat_id = context.job.context[3]

    send = False
    priceNow = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd').text
    priceNow = json.loads(priceNow)
    spot_price = f'{float(priceNow[crypto]["usd"])}'

    if sign == '<':
        if float(price) >= float(spot_price):
            send = True
    else:
        if float(price) <= float(spot_price):
            send = True

    if send:
        response = f'👋 {crypto.upper()} has surpassed ${price} and has just reached <b>${spot_price}</b>!'
        context.job.schedule_removal()
        context.bot.send_message(chat_id=chat_id, text=response)

# Top 10 crypto by market cap
def topTenCap(update, context):
    topByCap = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1").text
    topByCap = json.loads(topByCap)

    data = [['Name', '$','1d']]
    for x in range(10):
        data.append([topByCap[x]["name"], f'{round((topByCap[x]["current_price"]),2)}', f'{round((topByCap[x]["price_change_percentage_24h"]), 2)}%'])

    result = tabulate(data, headers='firstrow' , tablefmt='orgtbl' , numalign="center", stralign="center", floatfmt=".2f")
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="❇️ <b>Top 10 Crypto by Marketcap</b> ❇️")
    update.message.reply_text(f'<pre>{result}</pre>', parse_mode=ParseMode.HTML)

# Trending Cryptocurrencies
def trending(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="<pre>🔎 searching for result...</pre>")
    trend = cg.get_search_trending()
    data = [['Name', 'Price']]

    for x in range(7):
        coinId = trend["coins"][x]["item"]["id"]
        priceInUsd = cg.get_price(coinId, "usd")[coinId]["usd"]

        data.append([trend["coins"][x]["item"]["name"],priceInUsd])

    result = tabulate(data, headers="firstrow", tablefmt="orgtbl" , numalign="center", stralign="center", floatfmt=".2f")
    context.bot.editMessageText("❇️ <b>Trending Coins - (24h)</b> ❇️", chat_id=update.message.chat_id, message_id=(update.message.message_id)+1)
    update.message.reply_text(f'<pre>{result}</pre>', parse_mode=ParseMode.HTML)

# Global Cryptocurrency Stats
def globalStats(update, context):
    globalData = cg.get_global()
    response = f'❇️<b> Global Crypto Stats (updated)</b> ❇️ \n\n'
    response += f'<pre>▪️Active Crypto: {globalData["active_cryptocurrencies"]}</pre>\n'
    response += f'<pre>▪️Total Markets: {globalData["markets"]}</pre>\n'
    response += f'<pre>▪️MarketCap Changes: {round((globalData["market_cap_change_percentage_24h_usd"]), 2)}%</pre>\n'
    response += f'<pre>▪️Ongoing ICOs: {globalData["ongoing_icos"]}</pre>\n'
    response += f'<pre>▪️Last Updated: {datetime.fromtimestamp(globalData["updated_at"]).strftime("%H:%M")}</pre>'
    response += credit

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


# Crypto Details Check 
def checkDetails(update, context):
    if len(context.args) > 0:
        alter(context.args[0].lower())
        if alter.matched == "NO":
            response = errorAlert
            context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        else:
            market = cg.get_coins_markets(vs_currency="usd")
            for x in range(len(market)):
                if market[x]["id"] == alter.apiId:
                    response = f'❇️ <b>Cryptocurrency Profile</b> ❇️\n\n'
                    context.bot.send_photo(chat_id=update.message.chat_id, photo=f"{market[x]['image']}")
                    response += "<pre>========================</pre>\n"
                    response += f'<pre>▪️Name: {alter.cryptoNameFinal} ({(alter.cryptoSymbol).upper()})</pre>\n'
                    response += f'<pre>▪️Price: ${round((market[x]["current_price"]), 6)}</pre>\n'
                    response += f'<pre>▪️Market Rank: {market[x]["market_cap_rank"]}</pre>\n'
                    response += f'<pre>▪️Market Cap: {numerize.numerize(market[x]["market_cap"])}</pre>\n'
                    response += f'<pre>▪️24H Change: {round((market[x]["price_change_percentage_24h"]), 2)}%</pre>\n'
                    if market[x]["total_supply"] != None:
                        response += f'<pre>▪️Total Supply: {numerize.numerize(market[x]["total_supply"])}</pre>\n'
                    else:
                        response += f'<pre>▪️Total Supply: No Data</pre>\n'
                    response += f'<pre>▪️All-Time High: ${round((market[x]["ath"]), 6)}</pre>\n'
                    response += f'<pre>▪️All-Time Low: ${round((market[x]["atl"]), 6)}</pre>\n\n'
                    response += f'🌐 Get Price, Chart, and Info:\n'
                    response += f'<a href="https://coingecko.com/en/coins/{alter.apiId}">coingecko.com/en/coins/{alter.apiId}</a>\n'
                    response += "<pre>========================</pre>\n"
                    response += credit
                    break
                else:
                    response = errorAlert

            
            context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=response)


# Top 05 Crypto Exchanger
def top5Exchanger(update, context):
    m = cg.get_exchanges_list()
    response = f'❇️ <b>Top 05 Exchanger</b> ❇️\n\n'
    for x in range(5):
        response += f'<b>🔵 {m[x]["name"]}</b>\n'
        response += f'<pre>╠Country: {m[x]["country"]}</pre>\n'
        response += f'<pre>╠Established: {m[x]["year_established"]}</pre>\n'
        response += f'<pre>╠Website:</pre> <a href="{m[x]["url"]}">Click Here</a>\n\n'

    response += credit
    context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=response)


# Check Bot Status
def checkBot(update, context):
    gecko = cg.ping()
    if gecko["gecko_says"] == "(V3) To the Moon!":
        context.bot.send_message(chat_id=update.effective_chat.id, text="<b>✅ Cryptia is ALIVE.</b>")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="<b>❌ WTF! Why am I Down!</b>")


# Searching for alternate word...(id, name, symbol)
def alter(crypto):
    with open('crypto.json') as coinList:
        data = json.load(coinList)
    alter.matched = 'NO'
    for singleObject in data:
        cryptoApiId = singleObject.get('id')
        cryptoName = singleObject.get('name')
        cryptoSymbol = singleObject.get('symbol')
        if(cryptoApiId == crypto or cryptoSymbol == crypto or cryptoName == crypto):
            alter.apiId = cryptoApiId
            alter.cryptoNameFinal = cryptoName
            alter.cryptoSymbol = cryptoSymbol
            alter.matched = "YES"
            break


def main() -> None:
    updater = Updater(token=apiKey,defaults=Defaults(parse_mode=ParseMode.HTML))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', startCommand))
    dispatcher.add_handler(CommandHandler('alert', priceAlert))
    dispatcher.add_handler(CommandHandler('price', currentPrice))
    dispatcher.add_handler(CommandHandler('help', helpMenu))
    dispatcher.add_handler(CommandHandler('example', exampleMenu))
    dispatcher.add_handler(CommandHandler('top10', topTenCap))
    dispatcher.add_handler(CommandHandler('trending', trending))
    dispatcher.add_handler(CommandHandler('stats', globalStats))
    dispatcher.add_handler(CommandHandler('check', checkDetails))
    dispatcher.add_handler(CommandHandler('topx', top5Exchanger))
    dispatcher.add_handler(CommandHandler('status', checkBot))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()