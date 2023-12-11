import requests


base_url = "http://localhost:8080"

def reset_all():


    player_id = "meecles"

    r0 = requests.delete(
        url=f"{base_url}/reset-all"
    )
    print(r0.text)

    r1 = requests.post(
        url=f"{base_url}/api/player/{player_id}"
    )
    print(r1.text)

    r2 = requests.post(
        url=f"{base_url}/api/house/{player_id}"
    )


    print(r2.text)


reset_all()