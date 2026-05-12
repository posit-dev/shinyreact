[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{pkg}}"
version = "0.0.0.dev0"
description = "Prototype helper package exposing {{upstream_pkg}} to shinyreact"
requires-python = ">=3.10"
dependencies = [
    "shiny>=1.0.0",
    "htmltools>=0.5.0",
    "shinyreact",
]

[tool.hatch.build.targets.wheel]
packages = ["src/{{pkg}}"]

[tool.hatch.build.targets.wheel.force-include]
"src/{{pkg}}/www/{{pkg}}.js" = "{{pkg}}/www/{{pkg}}.js"
