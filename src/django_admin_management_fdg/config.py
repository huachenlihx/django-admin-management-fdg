"""Declarative configuration for management pages and endpoints."""
from dataclasses import dataclass
import re
from typing import Callable


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", value):
        raise ValueError("Names must start with a lowercase letter and contain lowercase letters, digits or underscores")


@dataclass(frozen=True)
class ManagementEndpoint:
    route: str
    name: str
    view: Callable
    methods: tuple[str, ...] = ("POST",)
    permission: str | None = None

    def __post_init__(self):
        _name(self.name)
        if not self.route or self.route.startswith('/') or not self.route.endswith('/') or '..' in self.route or '?' in self.route:
            raise ValueError("Endpoint route must be a nonempty relative Django path ending in / ")
        if not callable(self.view):
            raise ValueError("Endpoint view must be callable")
        methods = tuple(m.upper() for m in self.methods)
        if not methods or not set(methods) <= {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}:
            raise ValueError("Invalid HTTP methods")
        object.__setattr__(self, 'methods', methods)


@dataclass(frozen=True)
class ManagementPage:
    name: str
    label: str
    template_name: str | None = None
    view: Callable | None = None
    url_name: str | None = None
    permission: str | None = None
    icon: str = ""
    tooltip: str = ""
    color: str | None = None
    text_color: str | None = None
    button_style: str = "pill"
    order: int = 0
    endpoints: tuple[ManagementEndpoint, ...] = ()
    scope: str = "model"
    group: str = ""
    confirmation: str = ""
    audit: bool = False

    def __post_init__(self):
        _name(self.name)
        if self.scope not in {"model", "object"}:
            raise ValueError("Invalid scope")
        if self.scope == "object" and self.url_name:
            raise ValueError("Object pages require a managed template or view")
        if self.audit and self.url_name:
            raise ValueError("External views manage their own audit logging")
        if sum(x is not None for x in (self.template_name, self.view, self.url_name)) != 1:
            raise ValueError("Provide exactly one of template_name, view or url_name")
        if self.view is not None and not callable(self.view):
            raise ValueError("Page view must be callable")
        if not self.label:
            raise ValueError("Page label is required")
        if self.url_name and self.endpoints:
            raise ValueError("Existing named URLs manage their own endpoints")
        if self.button_style not in {"pill", "rounded", "square"}:
            raise ValueError("Invalid button_style")
        for color in (self.color, self.text_color):
            if color is not None and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError("Colors must be six-digit hex values")
        object.__setattr__(self, 'endpoints', tuple(self.endpoints))
        for field in ('name', 'route'):
            values = [getattr(e, field) for e in self.endpoints]
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate endpoint {field}")
