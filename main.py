import sys
from datetime import datetime, timedelta
import aiohttp
import asyncio
import platform


class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            raise HttpError(f"Connection error: {url}", str(err))


async def exchange_rate_for_day(index_day):
    d = datetime.now() - timedelta(days=int(index_day))
    shift = d.strftime("%d.%m.%Y")
    try:
        response = await request(
            f"https://api.privatbank.ua/p24api/exchange_rates?date={shift}"
        )
        rates = selected_rates(response)
        return {shift: rates}
    except HttpError as err:
        print(err)
        return {shift: "Error"}


def selected_rates(data):
    try:
        rates = data["exchangeRate"]
        rate_usd = next((rate for rate in rates if rate["currency"] == "USD"), None)
        rate_eur = next((rate for rate in rates if rate["currency"] == "EUR"), None)
        if rate_usd and rate_eur:
            return {
                "USD": {
                    "sale": rate_usd.get("saleRate", "N/A"),
                    "purchase": rate_usd.get("purchaseRate", "N/A"),
                },
                "EUR": {
                    "sale": rate_eur.get("saleRate", "N/A"),
                    "purchase": rate_eur.get("purchaseRate", "N/A"),
                },
            }
        else:
            return "Error: No USD or EUR rates for this day"
    except KeyError as e:
        raise ValueError(f"Invalid response structure: {e}")


async def main(days):
    if days < 1 or days > 10:
        print("Error: Invalid number of days. Please enter a number between 1 and 10.")
        return
    
    # Виконання запитів до API
    tasks = [exchange_rate_for_day(shift) for shift in range(1, int(days) + 1)]
    results = await asyncio.gather(*tasks)

    # Вивід результатів у потрібному форматі
    print("[")
    for result in results:
        print(f" {result},")
    print("]")


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if len(sys.argv) != 2:
        print(r"Usage: py .\main.py <number_of_days>")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("The number of days must be an integer.")
        sys.exit(1)

    asyncio.run(main(days))
