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
-   [Things to be Aware Of](gotchas.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#things-to-be-aware-of .section}
# Things to be Aware Of[¶](gotchas.html#things-to-be-aware-of "Link to this heading"){.headerlink}

::: {#tls-support .section}
## TLS Support[¶](gotchas.html#tls-support "Link to this heading"){.headerlink}

Support for Transport Layer Security (TLS) is increasingly important,
particularly on mobile platforms where an application is typically a
front end to a cloud-based server. As both Python and Qt implement
different APIs that support TLS, a PyQt application has a choice as to
which to use. This is particularly important when deploying an
application as the support may have to be included with, or built into,
the application itself.

Ideally the TLS implementation provided by the target would be used
(e.g. CryptoAPI on Windows, Secure Transport on macOS and iOS). This
would mean that security updates, including certificate updates, would
be handled by the vendor of the target operating system and could be
ignored by the application. Unfortunately there is no common TLS API.
The resolution to this problem is the subject of [PEP
543](https://www.python.org/dev/peps/pep-0543){.reference .external} but
that has yet to be implemented.

Python uses OpenSSL as its TLS implementation. Python v3.7.4 and later
use OpenSSL v1.1.1. Python v3.7.0 to v3.7.3 use OpenSSL v1.1.0. Earlier
versions of Python use OpenSSL v1.0.2. On Windows and macOS the standard
Python binary installers include copies of the corresponding OpenSSL
libraries.

Qt has support for the native TLS implementation on macOS and iOS but on
other platforms (except for Linux) a deployed application must include
it's own OpenSSL implementaion.
:::

::: {#crashes-on-exit .section}
## Crashes On Exit[¶](gotchas.html#crashes-on-exit "Link to this heading"){.headerlink}

When the Python interpreter leaves a *scope* (for example when it
returns from a function) it will potentially garbage collect all objects
local to that scope. The order in which it is done is, in effect,
random. Theoretically this can cause problems because it may mean that
the C++ destructors of any wrapped Qt instances are called in an order
that Qt isn't expecting and may result in a crash. However, in practice,
this is only likely to be a problem when the application is terminating.

As a way of mitigating this possiblity PyQt6 ensures that the C++
destructors of any
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} instances owned by Python are invoked before the destructor
of any
[QCoreApplication](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qcoreapplication.html){.reference
.external} instance is invoked. Note however that the order in which the
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} destructors are invoked is still random.
:::

::: {#keyword-arguments .section}
## Keyword Arguments[¶](gotchas.html#keyword-arguments "Link to this heading"){.headerlink}

PyQt6 supports the use of keyword arguments for optional arguments.
Although the PyQt6 and Qt documentation may indicate that an argument
has a particular name, you may find that PyQt6 actually uses a different
name. This is because the name of an argument is not part of the Qt API
and there is some inconsistency in the way that similar arguments are
named. Different versions of Qt may use a different name for an argument
which wouldn't affect the C++ API but would break the Python API.

The docstrings that PyQt6 generates for all classes, functions and
methods will contain the correct argument names.
:::

::: {#garbage-collection .section}
## Garbage Collection[¶](gotchas.html#garbage-collection "Link to this heading"){.headerlink}

C++ does not garbage collect unreferenced class instances, whereas
Python does. In the following C++ fragment both colours exist even
though the first can no longer be referenced from within the program:

::: {.highlight-default .notranslate}
::: highlight
    col = new QColor();
    col = new QColor();
:::
:::

In the corresponding Python fragment, the first colour is destroyed when
the second is assigned to [`col`{.docutils .literal
.notranslate}]{.pre}:

::: {.highlight-default .notranslate}
::: highlight
    col = QColor()
    col = QColor()
:::
:::

In Python, each colour must be assigned to different names. Typically
this is done within class definitions, so the code fragment would be
something like:

::: {.highlight-default .notranslate}
::: highlight
    self.col1 = QColor()
    self.col2 = QColor()
:::
:::

Sometimes a Qt class instance will maintain a pointer to another
instance and will eventually call the destructor of that second
instance. The most common example is that a
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} (and any of its sub-classes) keeps pointers to its children
and will automatically call their destructors. In these cases, the
corresponding Python object will also keep a reference to the
corresponding child objects.

So, in the following Python fragment, the first
[QLabel](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qlabel.html){.reference
.external} is not destroyed when the second is assigned to
[`lab`{.docutils .literal .notranslate}]{.pre} because the parent
[QWidget](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html){.reference
.external} still has a reference to it:

::: {.highlight-default .notranslate}
::: highlight
    parent = QWidget()
    lab = QLabel("First label", parent)
    lab = QLabel("Second label", parent)
:::
:::
:::

::: {#multiple-inheritance .section}
## Multiple Inheritance[¶](gotchas.html#multiple-inheritance "Link to this heading"){.headerlink}

It is not possible to define a new Python class that sub-classes from
more than one Qt class. The exception is classes specifically intended
to act as mixin classes such as those (like
[QQmlParserStatus](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlparserstatus.html){.reference
.external}) that implement Qt interfaces.
:::

::: {#access-to-protected-member-functions .section}
## Access to Protected Member Functions[¶](gotchas.html#access-to-protected-member-functions "Link to this heading"){.headerlink}

When an instance of a C++ class is not created from Python it is not
possible to access the protected member functions of that instance.
Attempts to do so will raise a Python exception. Also, any Python
methods corresponding to the instance's virtual member functions will
never be called.
:::

::: {#none-and-null .section}
## [`None`{.docutils .literal .notranslate}]{.pre} and [`NULL`{.docutils .literal .notranslate}]{.pre}[¶](gotchas.html#none-and-null "Link to this heading"){.headerlink}

Throughout PyQt6, the [`None`{.docutils .literal .notranslate}]{.pre}
value can be specified wherever [`NULL`{.docutils .literal
.notranslate}]{.pre} is acceptable to the underlying C++ code.

Equally, [`NULL`{.docutils .literal .notranslate}]{.pre} is converted to
[`None`{.docutils .literal .notranslate}]{.pre} whenever it is returned
by the underlying C++ code.
:::

::: {#support-for-void .section}
## Support for [`void`{.docutils .literal .notranslate}]{.pre}` `{.docutils .literal .notranslate}[`*`{.docutils .literal .notranslate}]{.pre}[¶](gotchas.html#support-for-void "Link to this heading"){.headerlink}

PyQt6 (actually SIP) represents [`void`{.docutils .literal
.notranslate}]{.pre}` `{.docutils .literal .notranslate}[`*`{.docutils
.literal .notranslate}]{.pre} values as objects of type
[[`voidptr`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr "PyQt6.sip.voidptr"){.reference
.internal}. Such values are often used to pass the addresses of external
objects between different Python modules. To make this easier, a Python
integer (or anything that Python can convert to an integer) can be used
whenever a [[`voidptr`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr "PyQt6.sip.voidptr"){.reference
.internal} is expected.

A [[`voidptr`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr "PyQt6.sip.voidptr"){.reference
.internal} may be converted to a Python integer by using the
[`int()`{.xref .py .py-func .docutils .literal .notranslate}]{.pre}
builtin function.

A [[`voidptr`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr "PyQt6.sip.voidptr"){.reference
.internal} may be converted to a Python string by using its
[[`asstring()`{.xref .py .py-meth .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr.asstring "PyQt6.sip.voidptr.asstring"){.reference
.internal} method. The [[`asstring()`{.xref .py .py-meth .docutils
.literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr.asstring "PyQt6.sip.voidptr.asstring"){.reference
.internal} method takes an optional integer argument which is the length
of the data in bytes.

A [[`voidptr`{.xref .py .py-class .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr "PyQt6.sip.voidptr"){.reference
.internal} may also be given a size (i.e. the size of the block of
memory that is pointed to) by calling its [[`setsize()`{.xref .py
.py-meth .docutils .literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/sip/sip-module.html#PyQt6.sip.voidptr.setsize "PyQt6.sip.voidptr.setsize"){.reference
.internal} method. If it has a size then it is also able to support
Python's buffer protocol and behaves like a Python [[`memoryview`{.xref
.py .py-class .docutils .literal
.notranslate}]{.pre}](https://docs.python.org/3/library/stdtypes.html#memoryview "(in Python v3.13)"){.reference
.external} object so that the block of memory can be treated as a
mutable list of bytes. It also means that the Python [[`struct`{.xref
.py .py-mod .docutils .literal
.notranslate}]{.pre}](https://docs.python.org/3/library/struct.html#module-struct "(in Python v3.13)"){.reference
.external} module can be used to unpack and pack binary data structures
in memory, memory mapped files or shared memory.
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

-   [Things to be Aware Of](gotchas.html#){.reference .internal}
    -   [TLS Support](gotchas.html#tls-support){.reference .internal}
    -   [Crashes On Exit](gotchas.html#crashes-on-exit){.reference
        .internal}
    -   [Keyword Arguments](gotchas.html#keyword-arguments){.reference
        .internal}
    -   [Garbage Collection](gotchas.html#garbage-collection){.reference
        .internal}
    -   [Multiple
        Inheritance](gotchas.html#multiple-inheritance){.reference
        .internal}
    -   [Access to Protected Member
        Functions](gotchas.html#access-to-protected-member-functions){.reference
        .internal}
    -   [[`None`{.docutils .literal .notranslate}]{.pre} and
        [`NULL`{.docutils .literal
        .notranslate}]{.pre}](gotchas.html#none-and-null){.reference
        .internal}
    -   [Support for [`void`{.docutils .literal
        .notranslate}]{.pre}` `{.docutils .literal
        .notranslate}[`*`{.docutils .literal
        .notranslate}]{.pre}](gotchas.html#support-for-void){.reference
        .internal}

</div>

<div>

#### Previous topic

[Support for Cooperative
Multi-inheritance](https://www.riverbankcomputing.com/static/Docs/PyQt6/multiinheritance.html "previous chapter")

</div>

<div>

#### Next topic

[Using Qt
Designer](https://www.riverbankcomputing.com/static/Docs/PyQt6/designer.html "next chapter")

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
-   [Things to be Aware Of](gotchas.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
