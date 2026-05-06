from shiny import reactive
from shinyreact import ReactApp, reactive_output


def server(input, output, session):  # noqa: ARG001
    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @reactive_output
    def txtout_title():
        return f"Hello, {greeting()}!"

    @reactive_output
    def txtout_count():
        return input.click_count()


app = ReactApp(server)
