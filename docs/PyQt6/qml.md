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
-   [Integrating Python and QML](qml.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#integrating-python-and-qml .section}
[]{#ref-integrating-qml}

# Integrating Python and QML[¶](qml.html#integrating-python-and-qml "Link to this heading"){.headerlink}

Qt includes QML as a means of declaratively describing a user interface
and using JavaScript as a scripting language within it. It is possible
to write complete standalone QML applications, or to combine them with
C++. PyQt6 allows QML to be integrated with Python in exactly the same
way. In particular:

-   Python types that are sub-classed from
    [QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
    .external} can be registered with QML.

-   Instances of registered Python types can be created and made
    available to QML scripts.

-   Instances of registered Python types can be created by QML scripts.

-   Singleton instances of registered Python types can be created
    automatically by a QML engine and made available to QML scripts.

-   QML scripts interact with Python objects through their properties,
    signals and slots.

-   Python properties, signals and slots can be given revision numbers
    that only those implemented by a specific version are made available
    to QML.

::: {.admonition .note}
Note

The PyQt support for QML requires knowledge of the internals of the C++
code that implements QML. This can (and does) change between Qt versions
and may mean that some features only work with specific Qt versions and
may not work at all with some future version of Qt.

It is recommended that, in an MVC architecture, QML should only be used
to implement the view. The model and controller should be implemented in
Python.
:::

::: {#registering-python-types .section}
## Registering Python Types[¶](qml.html#registering-python-types "Link to this heading"){.headerlink}

Registering Python types with QML is done in the same way is it is done
with C++ classes, i.e. using the
[qmlRegisterType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterType){.reference
.external},
[qmlRegisterSingletonType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterSingletonType){.reference
.external},
[qmlRegisterUncreatableType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterUncreatableType){.reference
.external} and
[qmlRegisterRevision()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterRevision){.reference
.external} functions.

In C++ these are template based functions that take the C++ class, and
sometimes a revision, as template arguments. In the Python
implementation these are simply passed as the first arguments to the
respective functions.
:::

::: {#a-simple-example .section}
## A Simple Example[¶](qml.html#a-simple-example "Link to this heading"){.headerlink}

The following simple example demonstates the implementation of a Python
class that is registered with QML. The class defines two properties. A
QML script is executed which creates an instance of the class and sets
the values of the properties. That instance is then returned to Python
which then prints the values of those properties.

Hopefully the comments are self explanatory:

::: {.highlight-default .notranslate}
::: highlight
    import sys

    from PyQt6.QtCore import pyqtProperty, QCoreApplication, QObject, QUrl
    from PyQt6.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine


    # This is the type that will be registered with QML.  It must be a
    # sub-class of QObject.
    class Person(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)

            # Initialise the value of the properties.
            self._name = ''
            self._shoeSize = 0

        # Define the getter of the 'name' property.  The C++ type of the
        # property is QString which Python will convert to and from a string.
        @pyqtProperty('QString')
        def name(self):
            return self._name

        # Define the setter of the 'name' property.
        @name.setter
        def name(self, name):
            self._name = name

        # Define the getter of the 'shoeSize' property.  The C++ type and
        # Python type of the property is int.
        @pyqtProperty(int)
        def shoeSize(self):
            return self._shoeSize

        # Define the setter of the 'shoeSize' property.
        @shoeSize.setter
        def shoeSize(self, shoeSize):
            self._shoeSize = shoeSize


    # Create the application instance.
    app = QCoreApplication(sys.argv)

    # Register the Python type.  Its URI is 'People', it's v1.0 and the type
    # will be called 'Person' in QML.
    qmlRegisterType(Person, 'People', 1, 0, 'Person')

    # Create a QML engine.
    engine = QQmlEngine()

    # Create a component factory and load the QML script.
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile('example.qml'))

    # Create an instance of the component.
    person = component.create()

    if person is not None:
        # Print the value of the properties.
        print("The person's name is %s." % person.name)
        print("They wear a size %d shoe." % person.shoeSize)
    else:
        # Print all errors that occurred.
        for error in component.errors():
            print(error.toString())
:::
:::

The following is the [`example.qml`{.docutils .literal
.notranslate}]{.pre} QML script that is executed:

::: {.highlight-default .notranslate}
::: highlight
    import People 1.0

    Person {
        name: "Bob Jones"
        shoeSize: 12
    }
:::
:::
:::

::: {#using-qqmllistproperty .section}
## Using QQmlListProperty[¶](qml.html#using-qqmllistproperty "Link to this heading"){.headerlink}

Defining list-based properties in Python that can be updated from QML is
done using the QQmlListProperty class. However the way it is used in
Python is slightly different to the way it is used in C++.

In the simple case QQmlListProperty wraps a Python list that is usually
an instance sttribute, for example:

::: {.highlight-default .notranslate}
::: highlight
    class BirthdayParty(QObject):

        def __init__(self, parent=None):
            super().__init__(parent)

            # The list which will be accessible from QML.
            self._guests = []

        @pyqtProperty(QQmlListProperty)
        def guests(self):
            return QQmlListProperty(Person, self, self._guests)
:::
:::

QML can now manipulate the Python list of [`Person`{.docutils .literal
.notranslate}]{.pre} instances. QQmlListProperty also acts as a proxy
for the Python list so that the following can be written:

::: {.highlight-default .notranslate}
::: highlight
    for guest in party.guests:
        print("Guest:", guest.name)
:::
:::

QQmlListProperty can also be used to wrap a *virtual* list. The
following code fragment is taken from the
[`chapter5-listproperties.py`{.docutils .literal .notranslate}]{.pre}
example included with PyQt6:

::: {.highlight-default .notranslate}
::: highlight
    class PieChart(QQuickItem):

        @pyqtProperty(QQmlListProperty)
        def slices(self):
            return QQmlListProperty(PieSlice, self,
                    append=lambda pie_ch, pie_sl: pie_sl.setParentItem(pie_ch))
:::
:::

[`PieChart`{.docutils .literal .notranslate}]{.pre} and
[`PieSlice`{.docutils .literal .notranslate}]{.pre} are Quick items that
are registered using
[qmlRegisterType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterType){.reference
.external}. Instances of both can be created from QML.
[`slices`{.docutils .literal .notranslate}]{.pre} is a property of
[`PieChart`{.docutils .literal .notranslate}]{.pre} that, as far as QML
is concerned, is a list of [`PieSlice`{.docutils .literal
.notranslate}]{.pre} instances.

The pyqtProperty decorator specifies that the property is a
QQmlListProperty, that its name is [`slices`{.docutils .literal
.notranslate}]{.pre} and that the [`slices()`{.docutils .literal
.notranslate}]{.pre} function is its getter.

The getter returns an instance of QQmlListProperty. This specifies that
elements of the list should be of type [`PieSlice`{.docutils .literal
.notranslate}]{.pre}, that the [`PieChart`{.docutils .literal
.notranslate}]{.pre} instance (i.e. [`self`{.docutils .literal
.notranslate}]{.pre}) has the property, and defines the callable that
will be invoked in order to append a new element to the list.

The [`append`{.docutils .literal .notranslate}]{.pre} callable is passed
two arguments: the object whose property is to be updated (i.e. the
[`PyChart`{.docutils .literal .notranslate}]{.pre} instance), and the
element to be appended (i.e. a [`PieSlice`{.docutils .literal
.notranslate}]{.pre} instance). Here we simply set the chart as the
slice's parent item. Note that there isn't actually a list anywhere -
this is because, in this particular example, one isn't needed.

The signature of the [`append`{.docutils .literal .notranslate}]{.pre}
callable is slightly different to that of the corresponding C++
function. In C++ the first argument is the QQmlListProperty instance
rather than the [`PyChart`{.docutils .literal .notranslate}]{.pre}
instance. The signatures of the [`at`{.docutils .literal
.notranslate}]{.pre}, [`clear`{.docutils .literal .notranslate}]{.pre}
and [`count`{.docutils .literal .notranslate}]{.pre} callables are
different in the same way.
:::

::: {#using-attached-properties .section}
## Using Attached Properties[¶](qml.html#using-attached-properties "Link to this heading"){.headerlink}

In order to use attached properties in C++, three steps need to be
taken.

-   A type that has attached properties must implement a static function
    called [`qmlAttachedProperties`{.docutils .literal
    .notranslate}]{.pre}. This is a factory that creates an instance of
    the properties object to attach.

-   A type that has attached properties needs to be defined as such
    using the [`QML_ATTACHED`{.docutils .literal .notranslate}]{.pre}
    macro.

-   The instance of an attached properties object is retrieved using the
    [`qmlAttachedPropertiesObject()`{.docutils .literal
    .notranslate}]{.pre} template function. The template type is the
    type that has the attached properties.

PyQt6 uses similar, but slightly simpler steps to achieve the same
thing.

-   When calling
    [qmlRegisterType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterType){.reference
    .external} to register a type that has attached properties the type
    of the properties object is passed as the
    [`attachedProperties`{.docutils .literal .notranslate}]{.pre}
    argument. This type will be used as the factory for creating an
    instance of the properties object.

-   The instance of an attached properties object is retrieved using the
    [qmlAttachedPropertiesObject()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlAttachedPropertiesObject){.reference
    .external} function in the same way that you would from C++. Just
    like
    [qmlRegisterType()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlRegisterType){.reference
    .external},
    [qmlAttachedPropertiesObject()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qtqml-module.html#qmlAttachedPropertiesObject){.reference
    .external} takes an additional first argument that is the type that,
    in C++, would be the template argument.

See the [`attach.py`{.docutils .literal .notranslate}]{.pre} example
included with PyQt6 for a complete example showing the use of attached
properties.
:::

::: {#using-property-value-sources .section}
## Using Property Value Sources[¶](qml.html#using-property-value-sources "Link to this heading"){.headerlink}

Property values sources are implemented in PyQt6 in the same way as they
are implemented in C++. Simply sub-class from both
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} and
[QQmlPropertyValueSource](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlpropertyvaluesource.html){.reference
.external} and provide an implementation of the
[setTarget()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlpropertyvaluesource.html#setTarget){.reference
.external} method.
:::

::: {#using-qqmlparserstatus .section}
## Using [QQmlParserStatus](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlparserstatus.html){.reference .external}[¶](qml.html#using-qqmlparserstatus "Link to this heading"){.headerlink}

Monitoring the QML parser status is implemented in PyQt6 in the same way
as it is implemented in C++. Simply sub-class from both
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external} and
[QQmlParserStatus](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlparserstatus.html){.reference
.external} and provide implementations of the
[classBegin()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlparserstatus.html#classBegin){.reference
.external} and
[componentComplete()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlparserstatus.html#componentComplete){.reference
.external} methods.
:::

::: {#writing-python-plugins-for-qmlscene .section}
## Writing Python Plugins for **qmlscene**[¶](qml.html#writing-python-plugins-for-qmlscene "Link to this heading"){.headerlink}

Qt allows plugins that implement QML modules to be written that can be
dynamically loaded by a C++ application (e.g. **qmlscene**). These
plugins are sub-classes of
[QQmlExtensionPlugin](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlextensionplugin.html){.reference
.external}. PyQt6 supports exactly the same thing and allows those
plugin to be written in Python. In other words it is possible to provide
QML extensions written in Python to a C++ application, and to provide
QML extensions written in C++ to a Python application.

PyQt6 provides a QML plugin called [`pyqt6qmlplugin`{.docutils .literal
.notranslate}]{.pre}. This acts as a wrapper around the Python code that
implements the plugin. It handles the loading of the Python interpreter,
locating and importing the Python module that contains the
implementation of
[QQmlExtensionPlugin](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlextensionplugin.html){.reference
.external}, creating an instance of that class, and calling the
instance's
[registerTypes()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtqml/qqmlextensionplugin.html#registerTypes){.reference
.external} method. By default the [`pyqt6qmlplugin`{.docutils .literal
.notranslate}]{.pre} is installed in the [`PyQt6`{.docutils .literal
.notranslate}]{.pre} sub-directory of your Qt installation's
[`plugin`{.docutils .literal .notranslate}]{.pre} directory.

::: {.admonition .note}
Note

[`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre} is the name of
the plugin as seen by QML. Its actual filename will be different and
operating system dependent.
:::

A QML extension module is a directory containing a file called
[`qmldir`{.docutils .literal .notranslate}]{.pre}. The file contains the
name of the module and the name of the plugin that implements the
module. It may also specify the directory containing the plugin. Usually
this isn't needed because the plugin is installed in the same directory.

Therefore, for a QML extension module called [`Charts`{.docutils
.literal .notranslate}]{.pre}, the contents of the [`qmldir`{.docutils
.literal .notranslate}]{.pre} file might be:

::: {.highlight-default .notranslate}
::: highlight
    module Charts
    plugin pyqt6qmlplugin /path/to/qt/plugins/PyQt6
:::
:::

The [`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre} expects to
find a Python module in the same directory with a filename ending with
[`plugin.py`{.docutils .literal .notranslate}]{.pre} or
[`plugin.pyw`{.docutils .literal .notranslate}]{.pre}. In this case the
name [`chartsplugin.py`{.docutils .literal .notranslate}]{.pre} would be
a sensible choice. Before importing this module
[`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre} first places
the name of the directory at the start of [`sys.path`{.xref .py .py-attr
.docutils .literal .notranslate}]{.pre}.

::: {.admonition .note}
Note

[`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre} has to locate
the directory containing the [`qmldir`{.docutils .literal
.notranslate}]{.pre} file itself. It does this using the same algorithm
used by QML, i.e. it searches some standard locations and locations
specified by the []{#index-0 .target}[`QML2_IMPORT_PATH`{.xref .std
.std-envvar .docutils .literal .notranslate}]{.pre} environment
variable. When using **qmlscene**, [`pyqt6qmlplugin`{.docutils .literal
.notranslate}]{.pre} will not know about any additional locations
specified by its [`-I`{.docutils .literal .notranslate}]{.pre} option.
Therefore, []{#index-1 .target}[`QML2_IMPORT_PATH`{.xref .std
.std-envvar .docutils .literal .notranslate}]{.pre} should always be
used to specify additional locations to search.
:::

Due to a limitation in QML it is not possible for multiple QML modules
to use the same C++ plugin. In C++ this is not a problem as there is a
one-to-one relationship between a module and the plugin. However, when
using Python, [`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre}
is used by every module. There are two solutions to this:

-   on operating systems that support it, place a symbolic link in the
    directory containing the [`qmldir`{.docutils .literal
    .notranslate}]{.pre} file that points to the actual
    [`pyqt6qmlplugin`{.docutils .literal .notranslate}]{.pre}

-   make a copy of [`pyqt6qmlplugin`{.docutils .literal
    .notranslate}]{.pre} in the directory containing the
    [`qmldir`{.docutils .literal .notranslate}]{.pre} file.

In both cases the contents of the [`qmldir`{.docutils .literal
.notranslate}]{.pre} file can be simplifed to:

::: {.highlight-default .notranslate}
::: highlight
    module Charts
    plugin pyqt6qmlplugin
:::
:::

PyQt6 provides an example that can be run as follows:

::: {.highlight-default .notranslate}
::: highlight
    cd /path/to/examples/quick/tutorials/extending/chapter6-plugins
    QML2_IMPORT_PATH=. /path/to/qmlscene app.qml
:::
:::

On Linux you may also need to set a value for the []{#index-2
.target}[`LD_LIBRARY_PATH`{.xref .std .std-envvar .docutils .literal
.notranslate}]{.pre} environment variable.
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

-   [Integrating Python and QML](qml.html#){.reference .internal}
    -   [Registering Python
        Types](qml.html#registering-python-types){.reference .internal}
    -   [A Simple Example](qml.html#a-simple-example){.reference
        .internal}
    -   [Using
        QQmlListProperty](qml.html#using-qqmllistproperty){.reference
        .internal}
    -   [Using Attached
        Properties](qml.html#using-attached-properties){.reference
        .internal}
    -   [Using Property Value
        Sources](qml.html#using-property-value-sources){.reference
        .internal}
    -   [Using
        QQmlParserStatus](qml.html#using-qqmlparserstatus){.reference
        .internal}
    -   [Writing Python Plugins for
        **qmlscene**](qml.html#writing-python-plugins-for-qmlscene){.reference
        .internal}

</div>

<div>

#### Previous topic

[Support for
QSettings](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt_qsettings.html "previous chapter")

</div>

<div>

#### Next topic

[Support for Cooperative
Multi-inheritance](https://www.riverbankcomputing.com/static/Docs/PyQt6/multiinheritance.html "next chapter")

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
-   [Integrating Python and QML](qml.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
