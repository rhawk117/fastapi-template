import json
import sys


def normalize_path_names(openapi_schema: dict) -> None:
    """
    Normalizes service names from "userGetAllUsers" to "getAllUsers"

    Taken directly from
        https://fastapi.tiangolo.com/advanced/generate-clients/#preprocess-the-openapi-specification-for-the-client-generator

    Arguments:
        openapi_schema {dict} -- the openapi schema of the app

    Returns:
        dict -- the normalized openapi schema
    """
    path_schema: dict[str, dict] = openapi_schema['paths']

    for path_data in path_schema.values():
        for operation in path_data.values():
            tag = operation['tags'][0]
            operation_id = operation['operationId']
            to_remove = f'{tag}-'
            new_operation_id = operation_id[len(to_remove) :]
            operation['operationId'] = new_operation_id


def main() -> None:
    from backend.app.build import create_app

    openapi_schema = create_app().openapi()
    normalize_path_names(openapi_schema)

    try:
        with open('openapi.json', 'w') as f:
            f.write(json.dumps(openapi_schema, indent=2))
    except Exception as e:
        print(f'Error writing OpenAPI schema to file: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
