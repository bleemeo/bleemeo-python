from bleemeo import Client, Resource, APIError, Graph


def create_dashboard():
    client = Client(load_from_env=True)

    try:
        resp_dashboard = client.create(
            Resource.DASHBOARD, {"name": "My dashboard"}, "id", "name"
        )
        dashboard = resp_dashboard.json()
        print(f"Successfully created dashboard: {dashboard}")
        print(f"View it on https://panel.bleemeo.com/dashboard/{dashboard['id']}")

        widget_body = {
            "dashboard": dashboard["id"],
            "title": "My widget",
            "graph": Graph.TEXT,
        }
        resp_widget = client.create(
            Resource.WIDGET, widget_body, "id", "title", "graph"
        )
        widget = resp_widget.json()
        print(f"Successfully created widget: {widget}")
    except APIError as e:
        print(f"API error: {e}:\n{e.response.text}")
    finally:
        client.logout()


if __name__ == "__main__":
    create_dashboard()
