from bleemeo import APIError, Client, Resource


def update_widget() -> None:
    client = Client(load_from_env=True)

    try:
        page, page_size = 1, 1
        resp_page = client.get_page(
            Resource.WIDGET,
            page=page,
            page_size=page_size,
            params={"title": "My widget", "fields": "id"},
        )
        results = resp_page.json()["results"]
        if len(results) == 0:
            print("Widget not found")
            return

        resp_widget = client.update(
            Resource.WIDGET,
            results[0]["id"],
            {"title": "This is my widget"},
            "id",
            "dashboard",
        )

        widget = resp_widget.json()
        print(f"Successfully updated widget: {widget}")
        print(f"Check it on https://panel.bleemeo.com/dashboard/{widget['dashboard']}")
    except APIError as e:
        print(f"API error: {e}:\n{e.response.text}")
    finally:
        client.logout()


if __name__ == "__main__":
    update_widget()
