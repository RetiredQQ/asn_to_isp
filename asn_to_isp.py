from bs4 import BeautifulSoup
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def extract(asn):
    summary_data = {}
    ip_ranges_data = {'ipv4': [], 'ipv6': []}
    print(f"Extracting: {asn.strip()}")

    url = f"https://ipinfo.io/AS{asn.strip()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, "html.parser")

        get_summary(soup, summary_data)
        get_ip_range(soup, ip_ranges_data)
        save_asn_json(asn.strip(), summary_data, ip_ranges_data)
        print(f"Done: {asn.strip()}")
    except requests.RequestException as e:
        print(f"Request failed for {asn.strip()}: {e}")
    except Exception as e:
        print(f"An error occurred for {asn.strip()}: {e}")

def save_asn_json(asn, summary_data, ip_ranges_data):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'asn', f'AS{asn}.json')
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump({
            'summary': summary_data,
            'ip_ranges': ip_ranges_data
        }, json_file, indent=2)

def main():
    threads = 100
    script_dir = os.path.dirname(os.path.abspath(__file__))
    asn_list_path = os.path.join(script_dir, 'asn', 'asnList.txt')

    try:
        with open(asn_list_path, "r") as file:
            asn_list = file.read().splitlines()  # Use splitlines to remove newlines
    except IOError as e:
        print(f"Error reading ASN list file: {e}")
        return

    with ThreadPoolExecutor(threads) as executor:
        futures = [executor.submit(extract, asn) for asn in asn_list]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred: {e}")

def get_summary(soup, summary_data):
    asn_summary = soup.find("table", class_="succinct-asn-info")
    if asn_summary:
        for row in asn_summary.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                key_name = cells[0].text.strip()
                key_value = cells[1].text.strip()
                summary_data[key_name] = key_value
    else:
        print("Summary table not found")

def get_ip_range(soup, ip_ranges_data):
    asn_ip_ranges = soup.find_all("table", class_="table-details")

    # Handle IPv4 table
    if len(asn_ip_ranges) >= 1:
        for row in asn_ip_ranges[0].find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                netblock = cells[0].text.strip()
                company = cells[1].text.strip()
                ip_ranges_data["ipv4"].append({
                    "netblock": netblock,
                    'company_name': company
                })

    # Handle IPv6 table (if it exists)
    if len(asn_ip_ranges) >= 2:
        for row in asn_ip_ranges[1].find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                netblock = cells[0].text.strip()
                company = cells[1].text.strip()
                ip_ranges_data["ipv6"].append({
                    "netblock": netblock,
                    'company_name': company
                })
    elif len(asn_ip_ranges) == 1:
        # Notify if IPv6 table is missing but IPv4 was processed
        print("IPv6 table not found, only IPv4 data extracted")

if __name__ == '__main__':
    main()
