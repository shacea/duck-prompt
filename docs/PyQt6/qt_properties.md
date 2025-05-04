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
-   [Support for Qt Properties](qt_properties.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#support-for-qt-properties .section}
# Support for Qt Properties[¶](qt_properties.html#support-for-qt-properties "Link to this heading"){.headerlink}

PyQt6 does not support the setting and getting of Qt properties as if
they were normal instance attributes. This is because the name of a
property often conflicts with the name of the property's getter method.

However, PyQt6 does support the initial setting of properties using
keyword arguments passed when an instance is created. For example:

::: {.highlight-default .notranslate}
::: highlight
    act = QAction("&Save", self, shortcut=QKeySequence.StandardKey.Save,
            statusTip="Save the document to disk", triggered=self.save)
:::
:::

The example also demonstrates the use of a keyword argument to connect a
signal to a slot.

PyQt6 also supports setting the values of properties (and connecting a
signal to a slot) using the [`pyqtConfigure()`{.xref .py .py-meth
.docutils .literal .notranslate}]{.pre} method. For example, the
following gives the same results as above:

::: {.highlight-default .notranslate}
::: highlight
    act = QAction("&Save", self)
    act.pyqtConfigure(shortcut=QKeySequence.StandardKey.Save,
            statusTip="Save the document to disk", triggered=self.save)
:::
:::

::: {#defining-new-qt-properties .section}
## Defining New Qt Properties[¶](qt_properties.html#defining-new-qt-properties "Link to this heading"){.headerlink}

A new Qt property may be defined using the pyqtProperty function. It is
used in the same way as the standard Python [`property()`{.docutils
.literal .notranslate}]{.pre} function. In fact, Qt properties defined
in this way also behave as Python properties.

[[PyQt6.QtCore.]{.pre}]{.sig-prename .descclassname}[[pyqtProperty]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[type]{.pre}]{.n}*[\[]{.optional}, *[[fget=None]{.pre}]{.n}*[\[]{.optional}, *[[fset=None]{.pre}]{.n}*[\[]{.optional}, *[[freset=None]{.pre}]{.n}*[\[]{.optional}, *[[fdel=None]{.pre}]{.n}*[\[]{.optional}, *[[doc=None]{.pre}]{.n}*[\[]{.optional}, *[[designable=True]{.pre}]{.n}*[\[]{.optional}, *[[scriptable=True]{.pre}]{.n}*[\[]{.optional}, *[[stored=True]{.pre}]{.n}*[\[]{.optional}, *[[user=False]{.pre}]{.n}*[\[]{.optional}, *[[constant=False]{.pre}]{.n}*[\[]{.optional}, *[[final=False]{.pre}]{.n}*[\[]{.optional}, *[[notify=None]{.pre}]{.n}*[\[]{.optional}, *[[revision=0]{.pre}]{.n}*[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[\]]{.optional}[)]{.sig-paren}[¶](qt_properties.html#PyQt6.QtCore.pyqtProperty "Link to this definition"){.headerlink}

:   Create a property that behaves as both a Python property and a Qt
    property.

    Parameters[:]{.colon}

    :   -   **type** -- the type of the property. It is either a Python
            type object or a string that is the name of a C++ type.

        -   **fget** -- the optional callable used to get the value of
            the property.

        -   **fset** -- the optional callable used to set the value of
            the property.

        -   **freset** -- the optional callable used to reset the value
            of the property to its default value.

        -   **fdel** -- the optional callable used to delete the
            property.

        -   **doc** -- the optional docstring of the property.

        -   **designable** -- optionally sets the Qt
            [`DESIGNABLE`{.docutils .literal .notranslate}]{.pre} flag.

        -   **scriptable** -- optionally sets the Qt
            [`SCRIPTABLE`{.docutils .literal .notranslate}]{.pre} flag.

        -   **stored** -- optionally sets the Qt [`STORED`{.docutils
            .literal .notranslate}]{.pre} flag.

        -   **user** -- optionally sets the Qt [`USER`{.docutils
            .literal .notranslate}]{.pre} flag.

        -   **constant** -- optionally sets the Qt [`CONSTANT`{.docutils
            .literal .notranslate}]{.pre} flag.

        -   **final** -- optionally sets the Qt [`FINAL`{.docutils
            .literal .notranslate}]{.pre} flag.

        -   **notify** -- the optional unbound notify signal.

        -   **revision** -- the revision exported to QML.

    Return type[:]{.colon}

    :   the property object.

It is also possible to use pyqtProperty as a decorator in the same way
as the standard Python [`property()`{.docutils .literal
.notranslate}]{.pre} function. The following example shows how to define
an [`int`{.docutils .literal .notranslate}]{.pre} property with a getter
and setter:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import QObject, pyqtProperty

    class Foo(QObject):

        def __init__(self):
            QObject.__init__(self)

            self._total = 0

        @pyqtProperty(int)
        def total(self):
            return self._total

        @total.setter
        def total(self, value):
            self._total = value
:::
:::

If you prefer the Qt terminology you may also use [`write`{.docutils
.literal .notranslate}]{.pre} instead of [`setter`{.docutils .literal
.notranslate}]{.pre} (and [`read`{.docutils .literal
.notranslate}]{.pre} instead of [`getter`{.docutils .literal
.notranslate}]{.pre}).
:::
:::

::: clearer
:::
:::
:::
:::

::: {.sphinxsidebar aria-label="Main" role="navigation"}
::: sphinxsidebarwrapper
<div>

### [Table of Contents](https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html)

-   [Support for Qt Properties](qt_properties.html#){.reference
    .internal}
    -   [Defining New Qt
        Properties](qt_properties.html#defining-new-qt-properties){.reference
        .internal}
        -   [[`PyQt6.QtCore.pyqtProperty()`{.docutils .literal
            .notranslate}]{.pre}](qt_properties.html#PyQt6.QtCore.pyqtProperty){.reference
            .internal}

</div>

<div>

#### Previous topic

[Support for Signals and
Slots](https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html "previous chapter")

</div>

<div>

#### Next topic

[Other Support for Dynamic
Meta-objects](https://www.riverbankcomputing.com/static/Docs/PyQt6/metaobjects.html "next chapter")

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
-   [Support for Qt Properties](qt_properties.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
