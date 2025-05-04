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
-   [Support for QVariant](pyqt_qvariant.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#support-for-qvariant .section}
[]{#ref-qvariant}

# Support for [QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference .external}[¶](pyqt_qvariant.html#support-for-qvariant "Link to this heading"){.headerlink}

PyQt6 can convert any Python object to a
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} and back again. Normally this is done automatically and
transparently so you don't even need to know of the existence of
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external}.

An invalid
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} is automatically converted to [`None`{.docutils .literal
.notranslate}]{.pre} and vice versa.

However there are some situations where you might need to exert more
control. For example you might want to distinguish between a
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} containing a C++ float value and one containing a C++ double
value.

However it is possible to temporarily suppress the automatic conversion
of a C++
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} to a Python object and to return a wrapped Python
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} instead by calling the [[`enableautoconversion()`{.xref .py
.py-func .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.enableautoconversion "PyQt6.sip.enableautoconversion"){.reference
.internal} function.

The actual value of a wrapped Python
[QVariant](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html){.reference
.external} is obtained by calling its
[value()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qvariant.html#value){.reference
.external} method.
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

[Support for Qt
Interfaces](https://www.riverbankcomputing.com/static/Docs/PyQt6/qt_interfaces.html "previous chapter")

</div>

<div>

#### Next topic

[Support for
QSettings](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt_qsettings.html "next chapter")

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
-   [Support for QVariant](pyqt_qvariant.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
