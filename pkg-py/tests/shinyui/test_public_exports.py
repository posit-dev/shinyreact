def test_public_exports():
    import shinyui as sui

    # Base/mixin class names (PascalCase, same as shiny.render.Renderer)
    assert sui.UiComponent
    assert sui.UiInput and sui.UiOutput and sui.UiLayout
    assert sui.HasInputValue and sui.Updatable and sui.AllowsChildren

    # Concrete classes (snake_case, same as shiny.render.data_frame)
    assert isinstance(sui.input_slider, type)
    assert isinstance(sui.input_select, type)
    assert isinstance(sui.input_action_button, type)
    assert isinstance(sui.output_code, type)
    assert isinstance(sui.output_plot, type)
    assert isinstance(sui.card, type)
    assert isinstance(sui.accordion, type)
    assert isinstance(sui.accordion_panel, type)
