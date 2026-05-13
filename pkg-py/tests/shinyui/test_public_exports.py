def test_public_exports():
    import shinyui as sui

    # Class names
    assert sui.UiComponent
    assert sui.UiInput and sui.UiOutput and sui.UiLayout
    assert sui.HasInputValue and sui.Updatable and sui.AllowsChildren
    assert sui.UiInputSlider and sui.UiInputSelect
    assert sui.UiOutputCode and sui.UiOutputPlot
    assert sui.UiCard and sui.UiAccordion and sui.UiAccordionPanel

    # Factory names
    assert callable(sui.input_slider)
    assert callable(sui.input_select)
    assert callable(sui.output_code)
    assert callable(sui.output_plot)
    assert callable(sui.card)
    assert callable(sui.accordion)
    assert callable(sui.accordion_panel)
