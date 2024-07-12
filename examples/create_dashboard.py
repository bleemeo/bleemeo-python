from bleemeo import APIError, Client, Graph, Resource


def create_dashboard() -> None:
    client = Client(load_from_env=True)

    try:
        resp_dashboard = client.create(Resource.DASHBOARD, {"name": "My dashboard"})
        dashboard = resp_dashboard.json()
        print(
            f"Successfully created dashboard: {dashboard['name']} ({dashboard['id']})"
        )
        print(f"View it on https://panel.bleemeo.com/dashboard/{dashboard['id']}")

        widget_body = {
            "dashboard": dashboard["id"],
            "title": "My widget",
            "graph": Graph.TEXT,
        }
        resp_widget = client.create(Resource.WIDGET, widget_body)
        widget = resp_widget.json()
        print(f"Successfully created widget: {widget['title']} ({widget['id']})")
    except APIError as e:
        print(f"API error: {e}")
    finally:
        client.logout()


if __name__ == "__main__":
    create_dashboard()
