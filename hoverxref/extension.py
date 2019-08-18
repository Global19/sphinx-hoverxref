import os
from docutils import nodes
from sphinx.domains.std import StandardDomain
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.fileutil import copy_asset
from sphinx.writers.html import HTMLTranslator

from . import version
from .registry import registry
from .utils import get_ref_xref_data, get_ref_obj_data

ASSETS_FILES = [
    'js/hoverxref.js_t',  # ``_t`` tells Sphinx this is a template
    'js/tooltipster.bundle.min.js',
    'css/tooltipster.custom.css',
    'css/tooltipster.bundle.min.css',
    'css/tooltipster-sideTip-shadow.min.css',
]

logger = logging.getLogger(__name__)


class HoverXRefStandardDomain(StandardDomain):

    """
    Override ``StandardDomain`` to save the values after the xref resolution.

    ``:ref:`` are treating as a different node in Sphinx
    (``sphinx.addnodes.pending_xref``). These nodes are translated to regular
    ``docsutils.nodes.reference`` for this domain class.

    Before loosing the data used to resolve the reference, our customized domain
    saves it inside the node itself to be used later by the ``HTMLTranslator``.
    """

    def _is_hoverxref_configured(self, env):
        project = env.config.hoverxref_project
        version = env.config.hoverxref_version
        return project and version

    def _inject_hoverxref_data(self, env, refnode, docname, labelid):
        refnode.replace_attr('classes', ['hoverxref'])

        project = env.config.hoverxref_project
        version = env.config.hoverxref_version
        refnode._hoverxref = {
            'data-project': project,
            'data-version': version,
            'data-doc': docname,
            'data-section': labelid,
        }

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        if typ == 'hoverxref':
            resolver = self._resolve_ref_xref
            return resolver(env, fromdocname, builder, typ, target, node, contnode)

        return super().resolve_xref(env, fromdocname, builder, typ, target, node, contnode)

    # NOTE: We could override more ``_resolve_xref`` method apply hover in more places
    def _resolve_ref_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        refnode = super()._resolve_ref_xref(env, fromdocname, builder, typ, target, node, contnode)
        if refnode is None:
            return

        if not self._is_hoverxref_configured(env) and typ == 'hoverxref':
            # Using ``:hoverxref:`` role without having hoverxref configured
            # properly. Log a warning.
            logger.warning('hoverxref role is not fully configured.')

        if self._is_hoverxref_configured(env) and (env.config.hoverxref_auto_ref or typ == 'hoverxref'):
            docname, labelid, _ = get_ref_xref_data(self, node, target)
            self._inject_hoverxref_data(env, refnode, docname, labelid)
            logger.info(
                ':ref: _hoverxref injected: fromdocname=%s %s',
                fromdocname,
                refnode._hoverxref,
            )
        return refnode

    def _resolve_obj_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        refnode = super()._resolve_obj_xref(env, fromdocname, builder, typ, target, node, contnode)
        if refnode is None:
            return

        if typ in registry.object_types:
            docname, labelid = get_ref_obj_data(self, node, typ, target)
            if self._is_hoverxref_configured(env):
                self._inject_hoverxref_data(env, refnode, docname, labelid)
                logger.info(
                    ':%s: _hoverxref injected: fromdocname=%s %s',
                    typ,
                    fromdocname,
                    refnode._hoverxref,
                )
        return refnode


class HoverXRefHTMLTranslator(HTMLTranslator):

    """
    Override ``HTMLTranslator`` to render extra data saved in reference nodes.

    It adds all the values saved under ``_hoverxref`` as attributes of the HTML
    reference tag.
    """

    def starttag(self, node, tagname, suffix='\n', empty=False, **attributes):
        if tagname == 'a' and hasattr(node, '_hoverxref'):
            attributes.update(node._hoverxref)
            logger.info('_hoverxref attributes: %s', attributes)

        elif tagname == 'dt':
            if node.parent.get('ids') == node.get('ids'):
                # Remove duplicated ids from node that were added by
                # ``confval_parse_node`` to the parent
                node.replace_attr('ids', [])

        return super().starttag(node, tagname, suffix, empty, **attributes)


def copy_asset_files(app, exception):
    """
    Copy all assets after build finished successfully.

    Assets that are templates (ends with ``_t``) are previously rendered using
    using all the configs starting with ``hoverxref_`` as a context.
    """
    if exception is None:  # build succeeded

        context = {}
        for attr in app.config.values:
            if attr.startswith('hoverxref_'):
                # First, add the default values to the context
                context[attr] = app.config.values[attr][0]

        for attr in dir(app.config):
            if attr.startswith('hoverxref_'):
                # Then, add the values that the user overrides
                context[attr] = getattr(app.config, attr)

        for f in ASSETS_FILES:
            path = os.path.join(os.path.dirname(__file__), '_static', f)
            copy_asset(
                path,
                os.path.join(app.outdir, '_static', f.split('.')[-1].replace('js_t', 'js')),
                context=context,
            )


def setup(app):
    """Setup ``hoverxref`` Sphinx extension."""

    # ``override`` was introduced in 1.8
    app.require_sphinx('1.8')

    default_project = os.environ.get('READTHEDOCS_PROJECT')
    default_version = os.environ.get('READTHEDOCS_VERSION')
    app.add_config_value('hoverxref_project', default_project, 'html')
    app.add_config_value('hoverxref_version', default_version, 'html')
    app.add_config_value('hoverxref_auto_ref', False, 'env')

    app.add_config_value('hoverxref_tooltip_api_host', 'https://readthedocs.org', 'env')
    app.add_config_value('hoverxref_tooltip_theme', ['tooltipster-shadow', 'tooltipster-shadow-custom'], 'env')
    app.add_config_value('hoverxref_tooltip_interactive', True, 'env')
    app.add_config_value('hoverxref_tooltip_maxwidth', 450, 'env')
    app.add_config_value('hoverxref_tooltip_animation', 'fade', 'env')
    app.add_config_value('hoverxref_tooltip_animation_duration', 0, 'env')
    app.add_config_value('hoverxref_tooltip_content', 'Loading...', 'env')
    app.add_config_value('hoverxref_tooltip_class', 'rst-content', 'env')

    app.set_translator('html', HoverXRefHTMLTranslator, override=True)

    # Read the Docs use ``readthedocs`` as the name of the build, so we need to
    # replace this as well
    app.set_translator('readthedocs', HoverXRefHTMLTranslator, override=True)

    # Add ``hoverxref`` role replicating the behavior of ``ref``
    app.add_role_to_domain(
        'std',
        'hoverxref',
        XRefRole(
            lowercase=True,
            innernodeclass=nodes.inline,
            warn_dangling=True,
        ),
    )

    app.add_domain(HoverXRefStandardDomain, override=True)

    app.connect('build-finished', copy_asset_files)

    for f in ASSETS_FILES:
        if f.endswith('.js') or f.endswith('.js_t'):
            app.add_js_file(f.replace('.js_t', '.js'))
        if f.endswith('.css'):
            app.add_css_file(f)

    return {
        'version': version,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
