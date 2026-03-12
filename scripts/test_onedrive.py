import requests
from auth_onedrive import get_token

def main():
    print("1) Pidiendo token...")
    token = get_token()
    print("2) Token OK (primeros 20 chars):", token[:20])

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/me/drive/root/children"

    print("3) Llamando Graph:", url)
    r = requests.get(url, headers=headers, timeout=60)

    print("4) Status code:", r.status_code)
    data = r.json()

    if "value" in data:
        print("Items encontrados:", len(data["value"]))
        for item in data["value"][:20]:
            print("-", item.get("name"))
    else:
        print(data)

if __name__ == "__main__":
    main()