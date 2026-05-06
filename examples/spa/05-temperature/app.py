from shinyreact import ReactApp, reactive_output


def server(input, output, session):  # noqa: ARG001
    @reactive_output
    def display():
        c = input.celsius()
        if c is None:
            return None
        f = round(c * 9 / 5 + 32, 1)
        zone = (
            "Freezing"
            if c <= 0
            else "Cold"
            if c <= 15
            else "Comfortable"
            if c <= 30
            else "Hot"
        )
        return {"celsius": c, "fahrenheit": f, "zone": zone}


app = ReactApp(server)
