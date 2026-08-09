from __future__ import annotations

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
import ipaddress
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET


SKIPPED_SCHEMES = {"data", "javascript", "mailto", "tel"}
HTTP_SCHEMES = {"http": 80, "https": 443}
HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class NormalizedBaseURL:
    url: str
    hostname: str
    port: int
    path: str


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []

    def handle_starttag(
        self,
        tag: str,
        attributes: list[tuple[str, str | None]],
    ) -> None:
        for name, value in attributes:
            if not value:
                continue
            if name in {"href", "src", "poster"} or (tag == "object" and name == "data"):
                self.references.append((name, value))


def _normalized_hostname(
    hostname: str,
    *,
    context: str,
    allow_idn: bool = False,
) -> str:
    if not hostname or any(character.isspace() for character in hostname):
        raise ValueError(f"{context} contains an invalid host")
    hostname = hostname.lower().rstrip(".")
    if not hostname or "%" in hostname:
        raise ValueError(f"{context} contains an invalid host")
    if not hostname.isascii():
        if not allow_idn:
            raise ValueError(f"{context} contains an invalid host")
        try:
            hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError as error:
            raise ValueError(f"{context} contains an invalid host") from error
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        labels = hostname.split(".")
        if any(not HOST_LABEL.fullmatch(label) for label in labels):
            raise ValueError(f"{context} contains an invalid host")
        return hostname
    return address.compressed


def _contains_decoded_dot_segment(path: str) -> bool:
    for segment in path.split("/"):
        decoded = segment
        for _ in range(4):
            next_value = unquote(decoded)
            if next_value == decoded:
                break
            decoded = next_value
            if decoded in {".", ".."}:
                return True
        if decoded in {".", ".."}:
            return True
    return False


def _port(parsed, *, context: str) -> int:
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"{context} contains an invalid port: {error}") from error
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(f"{context} contains an invalid port")
    return port if port is not None else HTTP_SCHEMES[parsed.scheme.lower()]


def normalize_base_url(base_url: str) -> NormalizedBaseURL:
    if (
        not isinstance(base_url, str)
        or not base_url
        or base_url != base_url.strip()
        or any(character.isspace() for character in base_url)
    ):
        raise ValueError("base URL must be a non-empty URL without raw whitespace")
    try:
        parsed = urlsplit(base_url)
        hostname = parsed.hostname
    except ValueError as error:
        raise ValueError(f"base URL is invalid: {error}") from error
    scheme = parsed.scheme.lower()
    if scheme not in HTTP_SCHEMES or not parsed.netloc or hostname is None:
        raise ValueError("base URL must include an http(s) scheme and host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("base URL must not include credentials")
    if "?" in base_url or "#" in base_url:
        raise ValueError("base URL must not include a query or fragment")
    normalized_hostname = _normalized_hostname(hostname, context="base URL")
    effective_port = _port(parsed, context="base URL")
    if _contains_decoded_dot_segment(parsed.path):
        raise ValueError("base URL contains a percent-decoded dot path segment")

    stripped_path = parsed.path.strip("/")
    normalized_path = f"/{stripped_path}/" if stripped_path else "/"
    authority_host = (
        f"[{normalized_hostname}]" if ":" in normalized_hostname else normalized_hostname
    )
    explicit_port = parsed.port
    authority = f"{authority_host}:{explicit_port}" if explicit_port is not None else authority_host
    normalized_url = urlunsplit((scheme, authority, normalized_path, "", ""))
    return NormalizedBaseURL(
        url=normalized_url,
        hostname=normalized_hostname,
        port=effective_port,
        path=normalized_path,
    )


def _reference_origin(parsed) -> tuple[str, int] | None:
    scheme = parsed.scheme.lower()
    if scheme not in HTTP_SCHEMES:
        return None
    if parsed.hostname is None:
        raise ValueError("reference URL must include a host")
    hostname = _normalized_hostname(
        parsed.hostname,
        context="reference URL",
        allow_idn=True,
    )
    port = _port(parsed, context="reference URL")
    return hostname, port


def reference_error(
    document_url: str,
    value: str,
    normalized_base: NormalizedBaseURL,
) -> str | None:
    try:
        parsed_value = urlsplit(value)
    except ValueError as error:
        return f"invalid URL {value!r}: {error}"
    if parsed_value.scheme.lower() in SKIPPED_SCHEMES:
        return None
    if "\\" in value:
        return f"{value!r} contains a backslash"
    try:
        resolved = urlsplit(urljoin(document_url, value))
    except ValueError as error:
        return f"invalid URL {value!r}: {error}"
    try:
        origin = _reference_origin(resolved)
    except ValueError as error:
        return f"invalid URL {value!r}: {error}"
    if origin != (normalized_base.hostname, normalized_base.port):
        return None

    path = resolved.path or "/"
    if _contains_decoded_dot_segment(path):
        return f"{value!r} contains a percent-decoded dot path segment"
    base_root = normalized_base.path.rstrip("/") or "/"
    if normalized_base.path == "/" or path == base_root or path.startswith(normalized_base.path):
        return None
    return (
        f"{value!r} resolves to {path!r} and escapes configured base path "
        f"{normalized_base.path!r}"
    )


def parse_html(document: Path) -> list[tuple[str, str]]:
    parser = ReferenceParser()
    parser.feed(document.read_text(encoding="utf-8"))
    return parser.references


def parse_xml(document: Path) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for element in ET.parse(document).iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in {"guid", "link", "loc", "url"} and element.text:
            value = element.text.strip()
            if value:
                references.append((local_name, value))
        for name, value in element.attrib.items():
            local_attribute = name.rsplit("}", 1)[-1]
            if local_attribute in {"href", "src", "url"} and value:
                references.append((local_attribute, value))
    return references


def check_site(site_root: Path, base_url: str) -> list[str]:
    normalized_base = normalize_base_url(base_url)
    site_root = Path(site_root).resolve()
    if not site_root.exists():
        return [f"site root does not exist: {site_root}"]
    if not site_root.is_dir():
        return [f"site root is not a directory: {site_root}"]

    documents = sorted([*site_root.rglob("*.html"), *site_root.rglob("*.xml")])
    if not documents:
        return ["site root contains no HTML or XML documents"]

    errors: list[str] = []
    for document in documents:
        try:
            if document.suffix.lower() == ".html":
                references = parse_html(document)
            else:
                references = parse_xml(document)
        except (ET.ParseError, LookupError) as error:
            errors.append(f"{document.relative_to(site_root)}: unable to parse XML: {error}")
            continue
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{document.relative_to(site_root)}: unable to read: {error}")
            continue

        relative = document.relative_to(site_root).as_posix()
        if relative.endswith("index.html"):
            relative = relative[: -len("index.html")]
        document_url = urljoin(normalized_base.url, relative)
        for attribute, value in references:
            error = reference_error(document_url, value, normalized_base)
            if error:
                errors.append(
                    f"{document.relative_to(site_root)}: {attribute}={value!r}: {error}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated URLs retain the configured base path"
    )
    parser.add_argument("site_root", type=Path)
    parser.add_argument("--base-url", required=True)
    arguments = parser.parse_args(argv)
    try:
        errors = check_site(arguments.site_root, arguments.base_url)
    except ValueError as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"base-path verification failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("base-path verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
