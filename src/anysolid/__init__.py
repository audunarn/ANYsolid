"""Lazy public API; numerical dependencies load on first use."""

__version__ = "0.1.0"
__all__ = ["SolidMesh", "PreparedSolid", "Recovery", "prepare"]


def prepare(mesh, material, *, order=2):
    """Prepare a region, loading the optional scikit-fem backend on demand."""
    from .backend import prepare as backend_prepare
    return backend_prepare(mesh, material, order=order)


def __getattr__(name):
    if name == "SolidMesh":
        from .mesh import SolidMesh
        return SolidMesh
    if name in {"PreparedSolid", "Recovery"}:
        from . import backend
        return getattr(backend, name)
    raise AttributeError(name)
