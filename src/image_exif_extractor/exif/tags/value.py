"""Type aliases for normalized Exif values and their JSON representation."""

type ExifValue = str | int | float | bytes | tuple[ExifValue, ...]

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
