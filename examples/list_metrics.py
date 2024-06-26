from bleemeo import Client, APIError, Resource


def list_metrics():
    with Client(load_from_env=True) as client:
        try:
            metric_iterator = client.iterate(
                Resource.METRIC, {"active": True, "fields": "id,label"}
            )
            for i, metric in enumerate(metric_iterator):
                if i < 200:
                    print(f"-> {metric}")
                elif i == 200:
                    print(
                        "Listing has more than 200 metrics, only the first 200 metrics are shown"
                    )
        except APIError as e:
            print(f"API error: {e}:\n{e.response.text}")


if __name__ == "__main__":
    list_metrics()
