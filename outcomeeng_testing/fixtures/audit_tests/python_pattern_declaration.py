case = {"root": "repo", "items": ["one"]}

if (computed := case.get("root")) is not None:
    pass

match case:
    case {"root": root, "items": [first, *rest], **extra}:
        pass
    case {"missing": missing} | {"alternate": missing}:
        pass
