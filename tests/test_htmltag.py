import os
import pytest
import shutil


srcdir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'examples',
    'default',
)

# srcdir with ``autosectionlabel_prefix_document = True`` config
prefixdocumentsrcdir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'examples',
    'prefixdocument',
)

# srcdir with ``Sphinx.add_object_type`` call
customobjectsrcdir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'examples',
    'custom-object',
)


@pytest.fixture(autouse=True, scope='function')
def remove_sphinx_build_output():
    """Remove _build/ folder, if exist."""
    for path in (srcdir, prefixdocumentsrcdir, customobjectsrcdir):
        build_path = os.path.join(path, '_build')
        if os.path.exists(build_path):
            shutil.rmtree(build_path)


@pytest.mark.sphinx(
    srcdir=srcdir,
)
def test_default_settings(app, status, warning):
    """The extension should not change the output if not configured."""
    app.build()
    path = app.outdir / 'index.html'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        '<a class="reference internal" href="chapter-i.html#chapter-i"><span class="std std-ref">This a :ref: to Chapter I</span></a>',
        '<a class="reference internal" href="chapter-i.html#section-i"><span class="std std-ref">This a :hoverxref: to Chapter I, Section I</span></a>',
    ]

    for chunk in chunks:
        assert chunk in content


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'hoverxref_project': 'myproject',
        'hoverxref_version': 'myversion',
    },
)
def test_project_version_settings(app, status, warning):
    app.build()
    path = app.outdir / 'index.html'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        '<a class="reference internal" href="chapter-i.html#chapter-i"><span class="std std-ref">This a :ref: to Chapter I</span></a>',
        '<a class="hoverxref reference internal" data-doc="chapter-i" data-project="myproject" data-section="section-i" data-version="myversion" href="chapter-i.html#section-i"><span class="std std-ref">This a :hoverxref: to Chapter I, Section I</span></a>',
    ]

    for chunk in chunks:
        assert chunk in content


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'hoverxref_project': 'myproject',
        'hoverxref_version': 'myversion',
    },
)
def test_js_render(app, status, warning):
    app.build()
    path = app.outdir / '_static' / 'js' / 'hoverxref.js'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        "theme: ['tooltipster-shadow', 'tooltipster-shadow-custom']",
        "interactive: true",
        "maxWidth: 450",
        "animation: 'fade'",
        "animationDuration: 0",
        "content: 'Loading...'",
        "var url = 'https://readthedocs.org' + '/api/v2/embed/?' + 'project=' + project + '&version=' + version + '&doc=' + doc + '&section=' + section;",
    ]

    for chunk in chunks:
        assert chunk in content


@pytest.mark.sphinx(
    srcdir=prefixdocumentsrcdir,
    confoverrides={
        'hoverxref_project': 'myproject',
        'hoverxref_version': 'myversion',
    },
)
def test_autosectionlabel_project_version_settings(app, status, warning):
    app.build()
    path = app.outdir / 'index.html'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        '<a class="reference internal" href="chapter-i.html#chapter-i"><span class="std std-ref">This a :ref: to Chapter I</span></a>.',
        '<a class="hoverxref reference internal" data-doc="chapter-i" data-project="myproject" data-section="chapter-i" data-version="myversion" href="chapter-i.html#chapter-i"><span class="std std-ref">This a :hoverxref: to Chapter I</span></a>',
    ]

    for chunk in chunks:
        assert chunk in content


@pytest.mark.sphinx(
    srcdir=customobjectsrcdir,
    confoverrides={},
)
def test_custom_object(app, status, warning):
    app.build()
    path = app.outdir / 'index.html'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        '<a class="hoverxref reference internal" data-doc="configuration" data-project="myproject" data-section="confval-conf-title" data-version="myversion" href="configuration.html#confval-conf-title"><code class="xref std std-confval docutils literal notranslate"><span class="pre">This</span> <span class="pre">is</span> <span class="pre">a</span> <span class="pre">:confval:</span> <span class="pre">to</span> <span class="pre">conf-title</span></code></a>',
        '<a class="hoverxref reference internal" data-doc="configuration" data-project="myproject" data-section="configuration" data-version="myversion" href="configuration.html#configuration"><span class="std std-ref">This is a :hoverxref: to Configuration document</span></a>',
    ]

    for chunk in chunks:
        assert chunk in content

    path = app.outdir / 'configuration.html'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        '\n'.join([
            # the id is in the ``dl`` tag and *not* in the ``dt``
            '<dl class="confval" id="confval-conf-title">',
            '<dt>',
            '<code class="descname">conf-title</code></dt>',
            '<dd><p>This is the description.</p>',
            '</dd></dl>',
        ]),
        '\n'.join([
            # the id is in the ``dl`` tag and *not* in the ``dt``
            '<dl class="confval" id="confval-conf-another-title">',
            '<dt>',
            '<code class="descname">conf-another-title</code></dt>',
            '<dd><p>This is another description.</p>',
            '</dd></dl>',
        ]),

    ]

    for chunk in chunks:
        assert chunk in content
