"""
High-performance async template manager for FastAPI with Jinja2.

This module provides a thread-safe, async-compatible template rendering system
with caching, lazy loading, and proper resource management.
"""

import dataclasses
import os
import weakref
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Request
import jinja2
from . import const


@dataclasses.dataclass(slots=True)
class TemplateOptions:
    static_dir: str = const.STATIC_DIR
    templates_dir: str = const.TEMPLATES_DIR
    auto_reload: bool = const.TEMPLATE_AUTO_RELOAD
    optimized: bool = True
    cache_size


class AsyncTemplateManager:
    """
    Thread-safe async template manager with performance optimizations.

    Features:
    - Async template rendering with ThreadPoolExecutor
    - LRU cache for compiled templates
    - Weak references for memory management
    - Context processors for global template variables
    - Automatic template reloading in debug mode
    """

    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir
        self._env: jinja2.Environment | None = None
        self._executor: ThreadPoolExecutor | None = None
        self._context_processors: dict[str, Any] = {}
        self._template_cache: weakref.WeakValueDictionary = (
            weakref.WeakValueDictionary()
        )
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        self._templates_dir.mkdir(parents=True, exist_ok=True)

        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self._templates_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            auto_reload=const.TEMPLATE_AUTO_RELOAD,
            enable_async=True, # idk why you wouldn't in FastAPI
            cache_size=const.TEMPLATE_CACHE_SIZE,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._env.globals.update(
            {
                "url_for": self._url_for,
                "static_url": self._static_url,
            }
        )
        max_workers = min(32, (os.cpu_count() or 1) + 4)
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="template-render-"
        )

        self._register_default_context_processors()

        self._initialized = True

    async def cleanup(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=True)
        self._template_cache.clear()
        self._initialized = False

    def add_context_processor(self, name: str, processor: Any) -> None:
        """Add a global context processor."""
        self._context_processors[name] = processor

    @lru_cache(maxsize=const.TEMPLATE_CACHE_SIZE)
    def _get_template(self, template_name: str) -> jinja2.Template:
        if not self._env:
            raise RuntimeError("Template manager not initialized")

        return self._env.get_template(template_name)

    def _build_context(
        self, request: Request, context: dict[str, Any]
    ) -> dict[str, Any]:
        template_context = {
            "request": request,
            **self._context_processors,
            **context,
        }
        return template_context

    async def render_template(
        self,
        template_name: str,
        request: Request,
        *,
        context: dict[str, Any] | None = None,
    ) -> str:
        if not self._initialized:
            raise RuntimeError("Template manager not initialized")

        if not self._env or not self._executor:
            raise RuntimeError("Template environment not configured")

        template_context = self._build_context(request, context or {})

        try:
            template = self._get_template(template_name)

            loaded_template = await template.render_async(**template_context)

        except jinja2.TemplateNotFound:
            raise
        except Exception as e:
            raise RuntimeError(f"Template rendering failed: {e}")

        return loaded_template

    async def render_string(
        self,
        template_string: str,
        request: Request,
        *,
        context: dict[str, Any] | None = None,
    ) -> str:
        if not self._env or not self._executor:
            raise RuntimeError("Template manager not initialized")

        template_context = self._build_context(request, context or {})

        template = self._env.from_string(template_string)
        return await template.render_async(**template_context)

    @staticmethod
    def _url_for(endpoint: str, **params: Any) -> str:
        """Generate URL for endpoint (placeholder implementation)."""
        # In a real app, you'd use FastAPI's URL generation
        return f"/{endpoint.lstrip('/')}"

    @staticmethod
    def _static_url(path: str) -> str:
        """Generate static file URL."""
        return f"/static/{path.lstrip('/')}"


template_manager = AsyncTemplateManager(Path(const.TEMPLATES_DIR))
