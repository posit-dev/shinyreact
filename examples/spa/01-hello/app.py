from shiny import reactive
from shiny.express import input
from shinyreact import reactive_output, set_page

set_page()


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
