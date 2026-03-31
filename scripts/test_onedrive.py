import requests
import sys
from auth_onedrive import get_token

def main():
    print("1) Pidiendo token...")
    try:
        token = get_token()
        print("2) Token OK (primeros 20 chars):", token[:20])
    except Exception as e:
        print(f"ERROR obteniendo token: {e}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/me/drive/root/children"

    print("3) Llamando Graph:", url)
    try:
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()

        print("4) Status code:", r.status_code)

        if "value" in data:
            print("Items encontrados:", len(data["value"]))
            for item in data["value"][:20]:
                print("-", item.get("name"))
        else:
            print(data)
    except requests.exceptions.RequestException as e:
        print(f"ERROR en solicitud: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR procesando respuesta: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()