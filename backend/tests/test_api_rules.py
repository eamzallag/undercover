"""The tech stack's rules for every API operation."""

from fastapi.routing import APIRoute

from backend.main import app


def routes() -> list[APIRoute]:
    return [route for route in app.routes if isinstance(route, APIRoute)]


def test_every_operation_has_an_operation_id():
    for route in routes():
        assert route.operation_id == route.name, route.path


def test_every_operation_has_a_one_line_docstring():
    for route in routes():
        doc = route.endpoint.__doc__
        assert doc, route.path
        assert "\n" not in doc.strip(), route.path


def test_no_operation_has_an_optional_input():
    schema = app.openapi()
    components = schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            for parameter in operation.get("parameters", []):
                assert parameter["required"], (path, parameter["name"])
            body = operation.get("requestBody")
            if body:
                assert body["required"], path
                ref = body["content"]["application/json"]["schema"]["$ref"]
                model = components[ref.split("/")[-1]]
                assert set(model["properties"]) == set(model["required"]), path
