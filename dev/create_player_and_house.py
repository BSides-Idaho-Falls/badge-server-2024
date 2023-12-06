import requests

base_url = "http://localhost:8080"


player_id = "meecles"

r0 = requests.post(
    url=f"{base_url}/api/player/{player_id}"
)

print(r0.text)


r1 = requests.post(
    url=f"{base_url}/api/house/{player_id}"
)


print(r1.text)

