from bleemeo import APIError, Client, Resource


def get_metric_data() -> None:
    client = Client(load_from_env=True)

    try:
        page, page_size = 1, 1
        resp_page = client.get_page(
            Resource.METRIC,
            page=page,
            page_size=page_size,
            params={"active": True},
        )

        results = resp_page.json()["results"]
        if len(results) == 0:
            print("No metric found")
            return

        metric = results[0]
        resp_data = client.do("GET", f"/{Resource.METRIC}{metric['id']}/data/")

        values = resp_data.json()["values"]
        print(f"Found {len(values)} data points for metric '{metric['label']}'")
    except APIError as e:
        print(f"API error: {e}:\n{e.response.text}")
    finally:
        client.logout()


if __name__ == "__main__":
    get_metric_data()
