"""Shared HTML-to-PDF rendering service.

Used by invoice and booking PDFs — and any future plugin PDF — to keep
rendering logic in one place. Templates are Jinja2 HTML; rendering uses
WeasyPrint. Plugins contribute their own template directories via
``register_plugin_template_path``.
"""
from __future__ import annotations

import os

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape


def build_default_template_env() -> Environment:
    """Create the default Jinja environment pointing at vbwd/templates/pdf/.

    Kept as a module-level factory so the DI container wiring stays short
    and tests can build throwaway envs without duplicating this code.
    """
    core_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "pdf",
    )
    os.makedirs(core_template_path, exist_ok=True)
    return Environment(
        loader=FileSystemLoader(core_template_path),
        autoescape=select_autoescape(["html", "xml"]),
    )


class PdfService:
    """Render Jinja2 HTML templates to PDF bytes via WeasyPrint.

    The service knows nothing about invoices or bookings — callers hand
    in a template name and a context dict. This keeps PdfService a single-
    responsibility renderer that is trivial to unit-test with a DictLoader.
    """

    def __init__(self, template_env: Environment, base_url: str | None = None) -> None:
        self._template_env = template_env
        self._base_url = base_url

    def render(self, template_name: str, context: dict) -> bytes:
        """Render a template to PDF bytes."""
        import weasyprint

        html_string = self._template_env.get_template(template_name).render(**context)
        return weasyprint.HTML(
            string=html_string,
            base_url=self._base_url,
        ).write_pdf()

    def register_plugin_template_path(self, path: str) -> None:
        """Extend the template loader with an additional filesystem path.

        Plugins call this during initialisation so their own PDF templates
        resolve via the shared env. Preserves the existing loader — new
        paths are searched after the core loader.
        """
        existing_loader = self._template_env.loader
        plugin_loader = FileSystemLoader(path)

        if isinstance(existing_loader, ChoiceLoader):
            self._template_env.loader = ChoiceLoader(
                list(existing_loader.loaders) + [plugin_loader]
            )
        elif existing_loader is not None:
            self._template_env.loader = ChoiceLoader([existing_loader, plugin_loader])
        else:
            self._template_env.loader = ChoiceLoader([plugin_loader])
