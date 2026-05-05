from pathlib import Path

import shinyjsonold as shinyjson
from shiny import reactive
from spa_app import SpaApp

_src_dir = Path(__file__).parent

# shiny.js
# react.js
# shiny-react.js
# shiny-shadcn.js, shiny-org.js
# ^^ Building blocks for your App
# custom.js
# ^^ More custom JS on top of the building blocks: card-barret
# Q: Requires prompt of "You can not use custom components!
#    You must use existing components from the building blocks."

# "It's not as big of an ask as before"

# Q: How do we teach users what goes in the server?
# This approach allows for "data manipulations"-only.
# Previous approaches required that the server knows EVERYTHING
# about the UI when dynamic UI was needed.
# - Big code smell, hard to maintain, hard to learn, hard to debug.

# Q: Workshops?
# We'll figure it out later. Having a nodejs already install and
# claude approved for all users in class seems feasible.
# The direction will shift from "How to code a full app by hand"
# to "How to describe your app UI and data interactions w/ Claude"


def server(input, output, session):

    # # app_card_data = reactive.value(name = "app_card_data")
    # # server_data = reactive.value()

    # x = reactive.value(0)

    # x()
    # x(x() + 1 ) # R

    # x()
    # x.get()
    # x.set(x() + 1 )

    # c(x, x_set) %<-% reactiveSignal(0)

    # x # value!
    # x() # getter

    # x # S7
    # x()
    # x.set()

    # x <- reactiveSignal(0, name = "x")
    # x # reactiveVal()
    # # hidden
    # observeEvent(x(),{
    #     updateSignal(x, x.name)
    # })

    # # # Ex: Garrick's conf app that has many columns of cards
    # # # and you can drag cards between columns.
    # # # You need to know when column updates are made.
    # # # Have the UI be within the app file, requires the author
    # # # to program the UI logic.
    # # # Given the complexity of the UI is all in the client,
    # # # this is MUCH EASIER.
    # # app_card_data = reactive.value()

    # # # Set's new "output" value for `card_data` on the client,
    # # # which triggers a re-render of any client-side UI that
    # # # depends on `card_data`
    # # @render.info
    # # def card_data():
    # #     return app_card_data()

    # input.CLIENT_VALUE()
    # ^^ value sent from client, e.g. card drag event
    #    with card id and new column id

    # app_card_data = reactive.signal(client_name = "card_data")

    # # app_card_data()
    # # app_card_data.get()

    # # app_card_data.set(new_value)

    # # only need actions against the data, not the UI
    # @reactive.effect(input.card_shuffled)
    # def _():
    #     id, pos = input.card_shuffled()
    #     update_card_position(app_card_data, id, pos)

    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @shinyjson.render
    def txtout_title():
        return f"Hello, {greeting()}!"

    @shinyjson.render
    def txtout_count():
        return input.click_count()


# app = shiny::SignalApp(_src_dir / "www", server)

# app = shiny::SpaApp(_src_dir / "www", server)
# app = company::SpaApp(_src_dir / "www", server)

app = SpaApp(_src_dir / "www", server)
