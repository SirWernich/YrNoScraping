# YrNoScraping

A simple Azure Pyton Function that uses BeautifulSoup to scrape yr.no for the hourly forecast for the current day and converts it into JSON.

## Usage

When deployed, call your Azure Function URL and append the location's code with query parameter `location`, example, for New York (`location=2-5128581`):

https://function-subdomain.azurewebsites.net/api/function-name?code=somefunkystring&location=2-5128581
