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
-   [Other Support for Dynamic Meta-objects](metaobjects.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#other-support-for-dynamic-meta-objects .section}
# Other Support for Dynamic Meta-objects[¶](metaobjects.html#other-support-for-dynamic-meta-objects "Link to this heading"){.headerlink}

PyQt6 creates a
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external} instance for any Python sub-class of
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} without the need for the equivalent of Qt's
[`Q_OBJECT`{.docutils .literal .notranslate}]{.pre} macro. Most of a
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external} is populated automatically by defining signals, slots and
properties as described in previous sections. In this section we cover
the ways in which the remaining parts of a
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external} are populated.

::: {#pyqtenum .section}
## [pyqtEnum()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtEnum){.reference .external}[¶](metaobjects.html#pyqtenum "Link to this heading"){.headerlink}

The
[pyqtEnum()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtEnum){.reference
.external} class decorator is used to decorate sub-classes of the Python
[[`Enum`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://docs.python.org/3/library/enum.html#enum.Enum "(in Python v3.13)"){.reference
.external} class so that they are published in the
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external}. The typical use in PyQt6 is to declare symbolic constants
that can be used by QML, and as the type of properties that can be set
in Qt Designer. For example:

::: {.highlight-default .notranslate}
::: highlight
    from enum import Enum, Flag

    from PyQt6.QtCore import pyqtEnum, QObject


    class Instruction(QObject):

        @pyqtEnum
        class Direction(Enum):
            Up, Down, Left, Right = range(4)

        @pyqtEnum
        class Status(Flag):
            Null = 0x00
            Urgent = 0x01
            Acknowledged = 0x02
            Completed = 0x04
:::
:::
:::

::: {#pyqtclassinfo .section}
## [pyqtClassInfo()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtClassInfo){.reference .external}[¶](metaobjects.html#pyqtclassinfo "Link to this heading"){.headerlink}

The
[pyqtClassInfo()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtClassInfo){.reference
.external} class decorator is used to specify a a name/value pair that
is placed in the class's
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external}. It is the equivalent of Qt's [`Q_CLASSINFO`{.xref .c
.c-macro .docutils .literal .notranslate}]{.pre} macro.

For example it is used by QML to define the default property of a class:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import pyqtClassInfo, QObject


    @pyqtClassInfo('DefaultProperty', 'guests')
    class BirthdayParty(QObject):

        pass
:::
:::

The decorator may be chained to define multiple name/value pairs.
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

-   [Other Support for Dynamic
    Meta-objects](metaobjects.html#){.reference .internal}
    -   [pyqtEnum](metaobjects.html#pyqtenum){.reference .internal}
    -   [pyqtClassInfo](metaobjects.html#pyqtclassinfo){.reference
        .internal}

</div>

<div>

#### Previous topic

[Support for Qt
Properties](https://www.riverbankcomputing.com/static/Docs/PyQt6/qt_properties.html "previous chapter")

</div>

<div>

#### Next topic

[Support for Qt
Interfaces](https://www.riverbankcomputing.com/static/Docs/PyQt6/qt_interfaces.html "next chapter")

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
-   [Other Support for Dynamic Meta-objects](metaobjects.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
