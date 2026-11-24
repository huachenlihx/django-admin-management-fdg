from .config import ManagementEndpoint, ManagementPage

__version__ = "1.0.2"
__all__ = ["ManagementPage", "ManagementEndpoint", "ManagementAdminMixin"]


def __getattr__(name):
    if name == "ManagementAdminMixin":
        from .mixins import ManagementAdminMixin
        return ManagementAdminMixin
    raise AttributeError(name)
