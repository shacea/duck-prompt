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
-   [Using Qt Designer](designer.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#using-qt-designer .section}
# Using Qt Designer[¶](designer.html#using-qt-designer "Link to this heading"){.headerlink}

Qt Designer is the Qt tool for designing and building graphical user
interfaces. It allows you to design widgets, dialogs or complete main
windows using on-screen forms and a simple drag-and-drop interface. It
has the ability to preview your designs to ensure they work as you
intended, and to allow you to prototype them with your users, before you
have to write any code.

Qt Designer uses XML [`.ui`{.docutils .literal .notranslate}]{.pre}
files to store designs and does not generate any code itself. Qt
includes the [`uic`{.docutils .literal .notranslate}]{.pre} utility that
generates the C++ code that creates the user interface. Qt also includes
the [`QUiLoader`{.docutils .literal .notranslate}]{.pre} class that
allows an application to load a [`.ui`{.docutils .literal
.notranslate}]{.pre} file and to create the corresponding user interface
dynamically.

PyQt6 does not wrap the [`QUiLoader`{.docutils .literal
.notranslate}]{.pre} class but instead includes the
[uic](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/uic/uic-module.html){.reference
.external} Python module. Like [`QUiLoader`{.docutils .literal
.notranslate}]{.pre} this module can load [`.ui`{.docutils .literal
.notranslate}]{.pre} files to create a user interface dynamically. Like
the **uic** utility it can also generate the Python code that will
create the user interface. PyQt6's **pyuic6** utility is a command line
interface to the
[uic](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/uic/uic-module.html){.reference
.external} module. Both are described in detail in the following
sections.

::: {#using-the-generated-code .section}
## Using the Generated Code[¶](designer.html#using-the-generated-code "Link to this heading"){.headerlink}

The code that is generated has an identical structure to that generated
by Qt's [`uic`{.docutils .literal .notranslate}]{.pre} and can be used
in the same way.

The code is structured as a single class that is derived from the Python
[`object`{.docutils .literal .notranslate}]{.pre} type. The name of the
class is the name of the toplevel object set in Designer with
[`Ui_`{.docutils .literal .notranslate}]{.pre} prepended. (In the C++
version the class is defined in the [`Ui`{.docutils .literal
.notranslate}]{.pre} namespace.) We refer to this class as the *form
class*.

The class contains a method called [`setupUi()`{.docutils .literal
.notranslate}]{.pre}. This takes a single argument which is the widget
in which the user interface is created. The type of this argument
(typically
[QDialog](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qdialog.html){.reference
.external},
[QWidget](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html){.reference
.external} or
[QMainWindow](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qmainwindow.html){.reference
.external}) is set in Designer. We refer to this type as the *Qt base
class*.

In the following examples we assume that a [`.ui`{.docutils .literal
.notranslate}]{.pre} file has been created containing a dialog and the
name of the
[QDialog](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qdialog.html){.reference
.external} object is [`ImageDialog`{.docutils .literal
.notranslate}]{.pre}. We also assume that the name of the file
containing the generated Python code is [`ui_imagedialog.py`{.file
.docutils .literal .notranslate}]{.pre}. The generated code can then be
used in a number of ways.

The first example shows the direct approach where we simply create a
simple application to create the dialog:

::: {.highlight-default .notranslate}
::: highlight
    import sys
    from PyQt6.QtWidgets import QApplication, QDialog
    from ui_imagedialog import Ui_ImageDialog

    app = QApplication(sys.argv)
    window = QDialog()
    ui = Ui_ImageDialog()
    ui.setupUi(window)

    window.show()
    sys.exit(app.exec())
:::
:::

The second example shows the single inheritance approach where we
sub-class
[QDialog](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qdialog.html){.reference
.external} and set up the user interface in the [`__init__()`{.docutils
.literal .notranslate}]{.pre} method:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtWidgets import QDialog
    from ui_imagedialog import Ui_ImageDialog

    class ImageDialog(QDialog):
        def __init__(self):
            super().__init__()

            # Set up the user interface from Designer.
            self.ui = Ui_ImageDialog()
            self.ui.setupUi(self)

            # Make some local modifications.
            self.ui.colorDepthCombo.addItem("2 colors (1 bit per pixel)")

            # Connect up the buttons.
            self.ui.okButton.clicked.connect(self.accept)
            self.ui.cancelButton.clicked.connect(self.reject)
:::
:::

The final example shows the multiple inheritance approach:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtGui import QDialog
    from ui_imagedialog import Ui_ImageDialog

    class ImageDialog(QDialog, Ui_ImageDialog):
        def __init__(self):
            super().__init__()

            # Set up the user interface from Designer.
            self.setupUi(self)

            # Make some local modifications.
            self.colorDepthCombo.addItem("2 colors (1 bit per pixel)")

            # Connect up the buttons.
            self.okButton.clicked.connect(self.accept)
            self.cancelButton.clicked.connect(self.reject)
:::
:::

For a full description see the Qt Designer Manual in the Qt
Documentation.
:::

::: {#pyuic6 .section}
## **pyuic6**[¶](designer.html#pyuic6 "Link to this heading"){.headerlink}

The **pyuic6** utility is a command line interface to the
[uic](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/uic/uic-module.html){.reference
.external} module. The command has the following syntax:

::: {.highlight-default .notranslate}
::: highlight
    pyuic6 [options] .ui-file
:::
:::

If [`.ui_file`{.file .docutils .literal .notranslate}]{.pre} is a file
then that file is converted. If it is a directory then every file with a
[`.ui`{.file .docutils .literal .notranslate}]{.pre} extension in the
directory is converted.

The full set of command line options is:

[]{#cmdoption-pyuic6-help}[[-h]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--help]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-h "Link to this definition"){.headerlink}

:   A help message is written to [`stdout`{.docutils .literal
    .notranslate}]{.pre}.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-version}[[-V]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--version]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-V "Link to this definition"){.headerlink}

:   The version number is written to [`stdout`{.docutils .literal
    .notranslate}]{.pre}.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-debug}[[-d]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--debug]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-d "Link to this definition"){.headerlink}

:   Show debug output.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-indent}[[-i]{.pre}]{.sig-name .descname}[ [\<N\>]{.pre}]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--indent]{.pre}]{.sig-name .descname}[ [\<N\>]{.pre}]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-i "Link to this definition"){.headerlink}

:   The Python code is generated using an indentation of
    [`<N>`{.docutils .literal .notranslate}]{.pre} spaces. If
    [`<N>`{.docutils .literal .notranslate}]{.pre} is 0 then a tab is
    used. The default is 4.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-output}[[-o]{.pre}]{.sig-name .descname}[ [\<FILE\>]{.pre}]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--output]{.pre}]{.sig-name .descname}[ [\<FILE\>]{.pre}]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-o "Link to this definition"){.headerlink}

:   If a single file is being converted then the Python code generated
    is written to the file [`<FILE>`{.docutils .literal
    .notranslate}]{.pre}. If [`<FILE>`{.docutils .literal
    .notranslate}]{.pre} is [`-`{.docutils .literal .notranslate}]{.pre}
    then it is written to [`stdout`{.docutils .literal
    .notranslate}]{.pre}. If a directory is converted then the generatee
    code is written to this directory.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-preview}[[-p]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--preview]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-p "Link to this definition"){.headerlink}

:   The GUI is created dynamically and displayed. No Python code is
    generated.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-max-workers}[[-w]{.pre}]{.sig-name .descname}[ [\<N\>]{.pre}]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--max-workers]{.pre}]{.sig-name .descname}[ [\<N\>]{.pre}]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-w "Link to this definition"){.headerlink}

:   A maximum of N worker processes are used when converting a
    directory. The default is 0.

```{=html}
<!-- -->
```

[]{#cmdoption-pyuic6-execute}[[-x]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[[,]{.pre} ]{.sig-prename .descclassname}[[\--execute]{.pre}]{.sig-name .descname}[]{.sig-prename .descclassname}[¶](designer.html#cmdoption-pyuic6-x "Link to this definition"){.headerlink}

:   The generated Python code includes a small amount of additional code
    that creates and displays the GUI when it is executes as a
    standalone application.

Note that code generated by **pyuic6** is not guaranteed to be
compatible with earlier versions of PyQt6. However, it is guaranteed to
be compatible with later versions. If you have no control over the
version of PyQt6 the users of your application are using then you should
run **pyuic6**, or call [[`compileUi()`{.xref .py .py-func .docutils
.literal
.notranslate}]{.pre}](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/uic/uic-module.html#PyQt6.uic.compileUi "PyQt6.uic.compileUi"){.reference
.internal}, as part of your installation process. Another alternative
would be to distribute the [`.ui`{.docutils .literal
.notranslate}]{.pre} files (perhaps as part of a resource file) and have
your application load them dynamically.
:::

::: {#writing-qt-designer-plugins .section}
[]{#ref-designer-plugins}

## Writing Qt Designer Plugins[¶](designer.html#writing-qt-designer-plugins "Link to this heading"){.headerlink}

Qt Designer can be extended by writing plugins. Normally this is done
using C++ but PyQt6 also allows you to write plugins in Python. Most of
the time a plugin is used to expose a custom widget to Designer so that
it appears in Designer's widget box just like any other widget. It is
possibe to change the widget's properties and to connect its signals and
slots.

It is also possible to add new functionality to Designer. See the Qt
documentation for the full details. Here we will concentrate on
describing how to write custom widgets in Python.

The process of integrating Python custom widgets with Designer is very
similar to that used with widget written using C++. However, there are
particular issues that have to be addressed.

-   Designer needs to have a C++ plugin that conforms to the interface
    defined by the [`QDesignerCustomWidgetInterface`{.docutils .literal
    .notranslate}]{.pre} class. (If the plugin exposes more than one
    custom widget then it must conform to the interface defined by the
    [`QDesignerCustomWidgetCollectionInterface`{.docutils .literal
    .notranslate}]{.pre} class.) In addition the plugin class must
    sub-class
    [QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
    .external} as well as the interface class. PyQt6 does not allow
    Python classes to be sub-classed from more than one Qt class.

-   Designer can only connect Qt signals and slots. It has no
    understanding of Python signals or callables.

-   Designer can only edit Qt properties that represent C++ types. It
    has no understanding of Python attributes or Python types.

PyQt6 provides the following components and features to resolve these
issues as simply as possible.

-   PyQt6's QtDesigner module includes additional classes (all of which
    have a [`QPy`{.docutils .literal .notranslate}]{.pre} prefix) that
    are already sub-classed from the necessary Qt classes. This avoids
    the need to sub-class from more than one Qt class in Python. For
    example, where a C++ custom widget plugin would sub-class from
    [QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
    .external} and [`QDesignerCustomWidgetInterface`{.docutils .literal
    .notranslate}]{.pre}, a Python custom widget plugin would instead
    sub-class from
    [QPyDesignerCustomWidgetPlugin](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtdesigner/qpydesignercustomwidgetplugin.html){.reference
    .external}.

-   PyQt6 installs a C++ plugin in Designer's plugin directory. It
    conforms to the interface defined by the
    [`QDesignerCustomWidgetCollectionInterface`{.docutils .literal
    .notranslate}]{.pre} class. It searches a configurable set of
    directories looking for Python plugins that implement a class
    sub-classed from
    [QPyDesignerCustomWidgetPlugin](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtdesigner/qpydesignercustomwidgetplugin.html){.reference
    .external}. Each class that is found is instantiated and the
    instance created is added to the custom widget collection.

    The []{#index-0 .target}[`PYQTDESIGNERPATH`{.xref .std .std-envvar
    .docutils .literal .notranslate}]{.pre} environment variable
    specifies the set of directories to search for plugins. Directory
    names are separated by a path separator (a semi-colon on Windows and
    a colon on other platforms). If a directory name is empty (ie. there
    are consecutive path separators or a leading or trailing path
    separator) then a set of default directories is automatically
    inserted at that point. The default directories are the
    [`python`{.file .docutils .literal .notranslate}]{.pre} subdirectory
    of each directory that Designer searches for its own plugins. If the
    environment variable is not set then only the default directories
    are searched. If a file's basename does not end with
    [`plugin`{.docutils .literal .notranslate}]{.pre} then it is
    ignored.

-   A Python custom widget may define new Qt signals using pyqtSignal.

-   A Python method may be defined as a new Qt slot by using the
    [pyqtSlot()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtSlot){.reference
    .external} decorator.

-   A new Qt property may be defined using the pyqtProperty function.

Note that the ability to define new Qt signals, slots and properties
from Python is potentially useful to plugins conforming to any plugin
interface and not just that used by Designer.

For a simple but complete and fully documented example of a custom
widget that defines new Qt signals, slots and properties, and its
plugin, look in the [`examples/designer/plugins`{.file .docutils
.literal .notranslate}]{.pre} directory of the PyQt6 source package. The
[`widgets`{.file .docutils .literal .notranslate}]{.pre} subdirectory
contains the [`pydemo.py`{.file .docutils .literal .notranslate}]{.pre}
custom widget and the [`python`{.file .docutils .literal
.notranslate}]{.pre} subdirectory contains its [`pydemoplugin.py`{.file
.docutils .literal .notranslate}]{.pre} plugin.
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

-   [Using Qt Designer](designer.html#){.reference .internal}
    -   [Using the Generated
        Code](designer.html#using-the-generated-code){.reference
        .internal}
    -   [**pyuic6**](designer.html#pyuic6){.reference .internal}
    -   [Writing Qt Designer
        Plugins](designer.html#writing-qt-designer-plugins){.reference
        .internal}

</div>

<div>

#### Previous topic

[Things to be Aware
Of](https://www.riverbankcomputing.com/static/Docs/PyQt6/gotchas.html "previous chapter")

</div>

<div>

#### Next topic

[Support for
Pickling](https://www.riverbankcomputing.com/static/Docs/PyQt6/pickle.html "next chapter")

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
-   [Using Qt Designer](designer.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
