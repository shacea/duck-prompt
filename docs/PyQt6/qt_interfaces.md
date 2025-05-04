::: {.related aria-label="Related" role="navigation"}
### Navigation

-   [Index](https://www.riverbankcomputing.com/static/Docs/PyQt6/genindex.html "General index"){accesskey="I"}
-   [Classes](https://www.riverbankcomputing.com/static/Docs/PyQt6/sip-classes.html "Index of all classes"){accesskey="C"}
    \|
-   [Modules](https://www.riverbankcomputing.com/static/Docs/PyQt6/module_index.html "Index of all modules"){accesskey="M"}
    \|
-   [PyQt Documentation
    v6.9.0](https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html)
    »
-   [Support for Qt Interfaces](qt_interfaces.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#support-for-qt-interfaces .section}
# Support for Qt Interfaces[¶](qt_interfaces.html#support-for-qt-interfaces "Link to this heading"){.headerlink}

PyQt6 does not, generally, support defining a class that inherits from
more than one Qt class. The exception is when inheriting from classes
that Qt defines as *interfaces*, for example
[QTextObjectInterface](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtgui/qtextobjectinterface.html){.reference
.external}.

A Qt interface is an abstract class contains only pure virtual methods
and is used as a mixin with (normally) a
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} sub-class. It is often used to define the interface that a
plugin must implement.

Note that PyQt6 does not need an equivalent of Qt's
[`Q_INTERFACES`{.xref .c .c-macro .docutils .literal
.notranslate}]{.pre} macro in order to use an interface class.

The [`textobject.py`{.docutils .literal .notranslate}]{.pre} example
included with PyQt6 demonstrates the use of an interface.
:::

::: clearer
:::
:::
:::
:::

::: {.sphinxsidebar aria-label="Main" role="navigation"}
::: sphinxsidebarwrapper
<div>

#### Previous topic

[Other Support for Dynamic
Meta-objects](https://www.riverbankcomputing.com/static/Docs/PyQt6/metaobjects.html "previous chapter")

</div>

<div>

#### Next topic

[Support for
QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt_qvariant.html "next chapter")

</div>

### Quick search {#searchlabel}

::: searchformwrapper
:::
:::
:::

::: clearer
:::
:::

::: {.related aria-label="Related" role="navigation"}
### Navigation

-   [Index](https://www.riverbankcomputing.com/static/Docs/PyQt6/genindex.html "General index")
-   [Classes](https://www.riverbankcomputing.com/static/Docs/PyQt6/sip-classes.html "Index of all classes")
    \|
-   [Modules](https://www.riverbankcomputing.com/static/Docs/PyQt6/module_index.html "Index of all modules")
    \|
-   [PyQt Documentation
    v6.9.0](https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html)
    »
-   [Support for Qt Interfaces](qt_interfaces.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
