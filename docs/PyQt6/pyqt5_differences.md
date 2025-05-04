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
-   [Differences Between PyQt6 and PyQt5](pyqt5_differences.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#differences-between-pyqt6-and-pyqt5 .section}
# Differences Between PyQt6 and PyQt5[¶](pyqt5_differences.html#differences-between-pyqt6-and-pyqt5 "Link to this heading"){.headerlink}

In this section we give an overview of the differences between PyQt6 and
PyQt5. This is not an exhaustive list and does not go into the detail of
the differences between the Qt v6 and Qt v5 APIs.

-   All named enums are now implemented as a sub-class of the standard
    Python [[`Enum`{.xref .py .py-class .docutils .literal
    .notranslate}]{.pre}](https://docs.python.org/3/library/enum.html#enum.Enum "(in Python v3.13)"){.reference
    .external} class. (PyQt5 used [[`IntEnum`{.xref .py .py-class
    .docutils .literal
    .notranslate}]{.pre}](https://docs.python.org/3/library/enum.html#enum.IntEnum "(in Python v3.13)"){.reference
    .external} for scoped enums and a custom type for traditional named
    enums).

-   Qt provides the [`QFlags`{.xref .cpp .cpp-class .docutils .literal
    .notranslate}]{.pre} template class as a type-safe way of using enum
    values that can be combined as a set of flags. The name of the class
    is often the plural form of the name of the enum. PyQt5 implements
    both of these as separate types. PyQt6 instead combines them as a
    single type, using the name of the enum, as a sub-class of
    [[`Flag`{.xref .py .py-class .docutils .literal
    .notranslate}]{.pre}](https://docs.python.org/3/library/enum.html#enum.Flag "(in Python v3.13)"){.reference
    .external}.

-   [`Q_CLASSINFO()`{.xref .py .py-func .docutils .literal
    .notranslate}]{.pre} has been replaced by the
    [pyqtClassInfo()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtClassInfo){.reference
    .external} class decorator.

-   [`Q_ENUM()`{.xref .py .py-func .docutils .literal
    .notranslate}]{.pre}, [`Q_ENUMS()`{.xref .py .py-func .docutils
    .literal .notranslate}]{.pre}, [`Q_FLAG()`{.xref .py .py-func
    .docutils .literal .notranslate}]{.pre} and [`Q_FLAGS()`{.xref .py
    .py-func .docutils .literal .notranslate}]{.pre} have been replaced
    by the
    [pyqtEnum()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtEnum){.reference
    .external} class decorator.

-   All [`exec_()`{.docutils .literal .notranslate}]{.pre} and
    [`print_()`{.docutils .literal .notranslate}]{.pre} methods have
    been removed.

-   [`qApp`{.xref .py .py-attr .docutils .literal .notranslate}]{.pre}
    has been removed.

-   The [`PYQT_CONFIGURATION`{.xref .py .py-const .docutils .literal
    .notranslate}]{.pre} dict has been removed.

-   The [`Qt`{.xref .py .py-mod .docutils .literal .notranslate}]{.pre}
    module has been removed.

-   The bindings for the (GPL licensed) Qt classes that implement
    support for network authorisation have moved out to a separate
    add-on project [`PyQt6-NetworkAuth`{.docutils .literal
    .notranslate}]{.pre}. This means that all of the libraries wrapped
    by PyQt6 itself are licensed under the LGPL.

-   **pylupdate6** is a completely new pure-Python implementation. It
    can no longer read a [`.pro`{.docutils .literal .notranslate}]{.pre}
    file in order to determine the names of [`.py`{.docutils .literal
    .notranslate}]{.pre} files to translate.

-   Support for Qt's resource system has been removed (i.e. there is no
    [`pyrcc6`{.docutils .literal .notranslate}]{.pre}).

-   Python v3.7 or later is required.

Qt v6 implements a number of functions from Qt v5 that are now marked as
being deprecated. These are not supported in PyQt6.
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

[Installing
PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/installation.html "previous chapter")

</div>

<div>

#### Next topic

[Support for Signals and
Slots](https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html "next chapter")

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
-   [Differences Between PyQt6 and PyQt5](pyqt5_differences.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
