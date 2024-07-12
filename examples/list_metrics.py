from bleemeo import APIError, Client, Resource


def list_metrics() -> None:
    with Client(load_from_env=True) as client:
        try:
            metric_iterator = client.iterate(Resource.METRIC, {"active": True})
            count = 0
            for metric in metric_iterator:
                count += 1
                if count <= 200:
                    print(f"-> {metric['label']} ({metric['id']})")
                elif count == 201:
                    print(
                        "Listing has more than 200 metrics, only the first 200 metrics are shown"
                    )

            print(f"Successfully retrieved {count} metrics from API")
        except APIError as e:
            print(f"API error: {e}:\n{e.response.text}")


if __name__ == "__main__":
    list_metrics()
