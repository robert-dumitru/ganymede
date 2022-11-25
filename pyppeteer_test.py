import asyncio
import logging
from pyppeteer import launch

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


async def main():
    browser = await launch(executablePath='/usr/bin/google-chrome-stable', headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto('https://example.com')
    await browser.close()


if __name__ == "__main__":
    print("Loaded script.")
    asyncio.run(main())
    print("Done with pyppeteer script.")
