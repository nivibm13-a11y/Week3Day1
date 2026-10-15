from bs4 import BeautifulSoup
import requests


def extract_schemes():
  url = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="
  print(f"Fetching data from {url}...")

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  response = requests.get(url, headers=headers)

  if response.status_code != 200:
    print(f"Failed to fetch page. Status code: {response.status_code}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  schemes_data = []

  # Strategy 1: Try parsing standard table rows
  for row in soup.find_all("tr"):
    cols = [col.text.strip() for col in row.find_all("td")]
    if len(cols) > 0 and any(cols):
      scheme_name = cols[0]
      details = " ".join(cols[1:]) if len(cols) > 1 else scheme_name
      schemes_data.append({"scheme_name": scheme_name, "details": details})

  # Strategy 2: If no table rows found, fallback to parsing links or list elements
  if not schemes_data:
    print("Table rows not found, checking list items and links...")
    for item in soup.find_all(["a", "li", "p"]):
      text = item.text.strip()
      if len(text) > 25:  # filter out short menu items
        schemes_data.append({"scheme_name": text[:60], "details": text})

  # Deduplicate results
  unique_schemes = {s["scheme_name"]: s for s in schemes_data}.values()
  final_schemes = list(unique_schemes)

  print(f"Successfully extracted {len(final_schemes)} schemes.")
  return final_schemes


if __name__ == "__main__":
  data = extract_schemes()
  for item in data[:3]:
    print(f"\nScheme: {item['scheme_name']}\nDetails: {item['details']}")