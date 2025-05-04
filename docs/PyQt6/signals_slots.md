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
-   [Support for Signals and Slots](signals_slots.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#support-for-signals-and-slots .section}
# Support for Signals and Slots[¶](signals_slots.html#support-for-signals-and-slots "Link to this heading"){.headerlink}

One of the key features of Qt is its use of signals and slots to
communicate between objects. Their use encourages the development of
reusable components.

A signal is emitted when something of potential interest happens. A slot
is a Python callable. If a signal is connected to a slot then the slot
is called when the signal is emitted. If a signal isn't connected then
nothing happens. The code (or component) that emits the signal does not
know or care if the signal is being used.

The signal/slot mechanism has the following features.

-   A signal may be connected to many slots.

-   A signal may also be connected to another signal.

-   Signal arguments may be any Python type.

-   A slot may be connected to many signals.

-   Connections may be direct (ie. synchronous) or queued (ie.
    asynchronous).

-   Connections may be made across threads.

-   Signals may be disconnected.

::: {#unbound-and-bound-signals .section}
## Unbound and Bound Signals[¶](signals_slots.html#unbound-and-bound-signals "Link to this heading"){.headerlink}

A signal (specifically an unbound signal) is a class attribute. When a
signal is referenced as an attribute of an instance of the class then
PyQt6 automatically binds the instance to the signal in order to create
a *bound signal*. This is the same mechanism that Python itself uses to
create bound methods from class functions.

A bound signal has [`connect()`{.docutils .literal .notranslate}]{.pre},
[`disconnect()`{.docutils .literal .notranslate}]{.pre} and
[`emit()`{.docutils .literal .notranslate}]{.pre} methods that implement
the associated functionality. It also has a [`signal`{.docutils .literal
.notranslate}]{.pre} attribute that is the signature of the signal that
would be returned by Qt's [`SIGNAL()`{.docutils .literal
.notranslate}]{.pre} macro.

A signal may be overloaded, ie. a signal with a particular name may
support more than one signature. A signal may be indexed with a
signature in order to select the one required. A signature is a sequence
of types. A type is either a Python type object or a string that is the
name of a C++ type. The name of a C++ type is automatically normalised
so that, for example, [`QVariant`{.docutils .literal
.notranslate}]{.pre} can be used instead of the non-normalised
[`const`{.docutils .literal .notranslate}]{.pre}` `{.docutils .literal
.notranslate}[`QVariant`{.docutils .literal
.notranslate}]{.pre}` `{.docutils .literal .notranslate}[`&`{.docutils
.literal .notranslate}]{.pre}.

If a signal is overloaded then it will have a default that will be used
if no index is given.

When a signal is emitted then any arguments are converted to C++ types
if possible. If an argument doesn't have a corresponding C++ type then
it is wrapped in a special C++ type that allows it to be passed around
Qt's meta-type system while ensuring that its reference count is
properly maintained.
:::

::: {#defining-new-signals-with-pyqtsignal .section}
## Defining New Signals with pyqtSignal[¶](signals_slots.html#defining-new-signals-with-pyqtsignal "Link to this heading"){.headerlink}

PyQt6 automatically defines signals for all Qt's built-in signals. New
signals can be defined as class attributes using the pyqtSignal factory.

[[PyQt6.QtCore.]{.pre}]{.sig-prename .descclassname}[[pyqtSignal]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[types]{.pre}]{.n}*[\[]{.optional}, *[[name]{.pre}]{.n}*[\[]{.optional}, *[[revision=0]{.pre}]{.n}*[\[]{.optional}, *[[arguments=\[\]]{.pre}]{.n}*[\]]{.optional}[\]]{.optional}[\]]{.optional}[)]{.sig-paren}[¶](signals_slots.html#PyQt6.QtCore.pyqtSignal "Link to this definition"){.headerlink}

:   Create one or more overloaded unbound signals as a class attribute.

    Parameters[:]{.colon}

    :   -   **types** -- the types that define the C++ signature of the
            signal. Each type may be a Python type object or a string
            that is the name of a C++ type. Alternatively each may be a
            sequence of type arguments. In this case each sequence
            defines the signature of a different signal overload. The
            first overload will be the default.

        -   **name** -- the name of the signal. If it is omitted then
            the name of the class attribute is used. This may only be
            given as a keyword argument.

        -   **revision** -- the revision of the signal that is exported
            to QML. This may only be given as a keyword argument.

        -   **arguments** -- the sequence of the names of the signal's
            arguments that is exported to QML. This may only be given as
            a keyword argument.

    Return type[:]{.colon}

    :   an unbound signal

The following example shows the definition of a number of new signals:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import QObject, pyqtSignal

    class Foo(QObject):

        # This defines a signal called 'closed' that takes no arguments.
        closed = pyqtSignal()

        # This defines a signal called 'rangeChanged' that takes two
        # integer arguments.
        range_changed = pyqtSignal(int, int, name='rangeChanged')

        # This defines a signal called 'valueChanged' that has two overloads,
        # one that takes an integer argument and one that takes a QString
        # argument.  Note that because we use a string to specify the type of
        # the QString argument then this code will run under Python v2 and v3.
        valueChanged = pyqtSignal([int], ['QString'])
:::
:::

New signals should only be defined in sub-classes of
[QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
.external}. They must be part of the class definition and cannot be
dynamically added as class attributes after the class has been defined.

New signals defined in this way will be automatically added to the
class's
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external}. This means that they will appear in Qt Designer and can be
introspected using the
[QMetaObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject.html){.reference
.external} API.

Overloaded signals should be used with care when an argument has a
Python type that has no corresponding C++ type. PyQt6 uses the same
internal C++ class to represent such objects and so it is possible to
have overloaded signals with different Python signatures that are
implemented with identical C++ signatures with unexpected results. The
following is an example of this:

::: {.highlight-default .notranslate}
::: highlight
    class Foo(QObject):

        # This will cause problems because each has the same C++ signature.
        valueChanged = pyqtSignal([dict], [list])
:::
:::
:::

::: {#connecting-disconnecting-and-emitting-signals .section}
## Connecting, Disconnecting and Emitting Signals[¶](signals_slots.html#connecting-disconnecting-and-emitting-signals "Link to this heading"){.headerlink}

Signals are connected to slots using the [[`connect()`{.xref .py
.py-meth .docutils .literal
.notranslate}]{.pre}](signals_slots.html#connect "connect"){.reference
.internal} method of a bound signal.

[[connect]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[slot]{.pre}]{.n}*[\[]{.optional}, *[[type=PyQt6.QtCore.Qt.AutoConnection]{.pre}]{.n}*[\[]{.optional}, *[[no_receiver_check=False]{.pre}]{.n}*[\]]{.optional}[\]]{.optional}[)]{.sig-paren} [[→]{.sig-return-icon} [[PyQt6.QtCore.QMetaObject.Connection]{.pre}]{.sig-return-typehint}]{.sig-return}[¶](signals_slots.html#connect "Link to this definition"){.headerlink}

:   Connect a signal to a slot. An exception will be raised if the
    connection failed.

    Parameters[:]{.colon}

    :   -   **slot** -- the slot to connect to, either a Python callable
            or another bound signal.

        -   **type** -- the type of the connection to make.

        -   **no_receiver_check** -- suppress the check that the
            underlying C++ receiver instance still exists and deliver
            the signal anyway.

    Returns[:]{.colon}

    :   a
        [Connection](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject-connection.html){.reference
        .external} object which can be passed to [[`disconnect()`{.xref
        .py .py-meth .docutils .literal
        .notranslate}]{.pre}](signals_slots.html#disconnect "disconnect"){.reference
        .internal}. This is the only way to disconnect a connection to a
        lambda function.

Signals are disconnected from slots using the [[`disconnect()`{.xref .py
.py-meth .docutils .literal
.notranslate}]{.pre}](signals_slots.html#disconnect "disconnect"){.reference
.internal} method of a bound signal.

[[disconnect]{.pre}]{.sig-name .descname}[(]{.sig-paren}[\[]{.optional}*[[slot]{.pre}]{.n}*[\]]{.optional}[)]{.sig-paren}[¶](signals_slots.html#disconnect "Link to this definition"){.headerlink}

:   Disconnect one or more slots from a signal. An exception will be
    raised if the slot is not connected to the signal or if the signal
    has no connections at all.

    Parameters[:]{.colon}

    :   **slot** -- the optional slot to disconnect from, either a
        [Connection](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qmetaobject-connection.html){.reference
        .external} object returned by [[`connect()`{.xref .py .py-meth
        .docutils .literal
        .notranslate}]{.pre}](signals_slots.html#connect "connect"){.reference
        .internal}, a Python callable or another bound signal. If it is
        omitted then all slots connected to the signal are disconnected.

Signals are emitted from using the [[`emit()`{.xref .py .py-meth
.docutils .literal
.notranslate}]{.pre}](signals_slots.html#emit "emit"){.reference
.internal} method of a bound signal.

[[emit]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[\\\*args]{.pre}]{.n}*[)]{.sig-paren}[¶](signals_slots.html#emit "Link to this definition"){.headerlink}

:   Emit a signal.

    Parameters[:]{.colon}

    :   **args** -- the optional sequence of arguments to pass to any
        connected slots.

The following code demonstrates the definition, connection and emit of a
signal without arguments:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import QObject, pyqtSignal

    class Foo(QObject):

        # Define a new signal called 'trigger' that has no arguments.
        trigger = pyqtSignal()

        def connect_and_emit_trigger(self):
            # Connect the trigger signal to a slot.
            self.trigger.connect(self.handle_trigger)

            # Emit the signal.
            self.trigger.emit()

        def handle_trigger(self):
            # Show that the slot has been called.

            print "trigger signal received"
:::
:::

The following code demonstrates the connection of overloaded signals:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtWidgets import QComboBox

    class Bar(QComboBox):

        def connect_activated(self):
            # The PyQt6 documentation will define what the default overload is.
            # In this case it is the overload with the single integer argument.
            self.activated.connect(self.handle_int)

            # For non-default overloads we have to specify which we want to
            # connect.  In this case the one with the single string argument.
            # (Note that we could also explicitly specify the default if we
            # wanted to.)
            self.activated[str].connect(self.handle_string)

        def handle_int(self, index):
            print "activated signal passed integer", index

        def handle_string(self, text):
            print "activated signal passed QString", text
:::
:::
:::

::: {#connecting-signals-using-keyword-arguments .section}
## Connecting Signals Using Keyword Arguments[¶](signals_slots.html#connecting-signals-using-keyword-arguments "Link to this heading"){.headerlink}

It is also possible to connect signals by passing a slot as a keyword
argument corresponding to the name of the signal when creating an
object, or using the [`pyqtConfigure()`{.xref .py .py-meth .docutils
.literal .notranslate}]{.pre} method. For example the following three
fragments are equivalent:

::: {.highlight-default .notranslate}
::: highlight
    act = QAction("Action", self)
    act.triggered.connect(self.on_triggered)

    act = QAction("Action", self, triggered=self.on_triggered)

    act = QAction("Action", self)
    act.pyqtConfigure(triggered=self.on_triggered)
:::
:::
:::

::: {#the-pyqtslot-decorator .section}
## The [pyqtSlot()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtSlot){.reference .external} Decorator[¶](signals_slots.html#the-pyqtslot-decorator "Link to this heading"){.headerlink}

Although PyQt6 allows any Python callable to be used as a slot when
connecting signals, it is sometimes necessary to explicitly mark a
Python method as being a Qt slot and to provide a C++ signature for it.
PyQt6 provides the
[pyqtSlot()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtSlot){.reference
.external} function decorator to do this.

[[PyQt6.QtCore.]{.pre}]{.sig-prename .descclassname}[[pyqtSlot]{.pre}]{.sig-name .descname}[(]{.sig-paren}*[[types]{.pre}]{.n}*[\[]{.optional}, *[[name]{.pre}]{.n}*[\[]{.optional}, *[[result]{.pre}]{.n}*[\[]{.optional}, *[[revision=0]{.pre}]{.n}*[\]]{.optional}[\]]{.optional}[\]]{.optional}[)]{.sig-paren}[¶](signals_slots.html#PyQt6.QtCore.pyqtSlot "Link to this definition"){.headerlink}

:   Decorate a Python method to create a Qt slot.

    Parameters[:]{.colon}

    :   -   **types** -- the types that define the C++ signature of the
            slot. Each type may be a Python type object or a string that
            is the name of a C++ type.

        -   **name** -- the name of the slot that will be seen by C++.
            If omitted the name of the Python method being decorated
            will be used. This may only be given as a keyword argument.

        -   **revision** -- the revision of the slot that is exported to
            QML. This may only be given as a keyword argument.

        -   **result** -- the type of the result and may be a Python
            type object or a string that specifies a C++ type. This may
            only be given as a keyword argument.

Connecting a signal to a decorated Python method also has the advantage
of reducing the amount of memory used and is slightly faster.

For example:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import QObject, pyqtSlot

    class Foo(QObject):

        @pyqtSlot()
        def foo(self):
            """ C++: void foo() """

        @pyqtSlot(int, str)
        def foo(self, arg1, arg2):
            """ C++: void foo(int, QString) """

        @pyqtSlot(int, name='bar')
        def foo(self, arg1):
            """ C++: void bar(int) """

        @pyqtSlot(int, result=int)
        def foo(self, arg1):
            """ C++: int foo(int) """

        @pyqtSlot(int, QObject)
        def foo(self, arg1):
            """ C++: int foo(int, QObject *) """
:::
:::

It is also possible to chain the decorators in order to define a Python
method several times with different signatures. For example:

::: {.highlight-default .notranslate}
::: highlight
    from PyQt6.QtCore import QObject, pyqtSlot

    class Foo(QObject):

        @pyqtSlot(int)
        @pyqtSlot('QString')
        def valueChanged(self, value):
            """ Two slots will be defined in the QMetaObject. """
:::
:::
:::

::: {#the-pyqt-pyobject-signal-argument-type .section}
## The [`PyQt_PyObject`{.docutils .literal .notranslate}]{.pre} Signal Argument Type[¶](signals_slots.html#the-pyqt-pyobject-signal-argument-type "Link to this heading"){.headerlink}

It is possible to pass any Python object as a signal argument by
specifying [`PyQt_PyObject`{.docutils .literal .notranslate}]{.pre} as
the type of the argument in the signature. For example:

::: {.highlight-default .notranslate}
::: highlight
    finished = pyqtSignal('PyQt_PyObject')
:::
:::

This would normally be used for passing objects where the actual Python
type isn't known. It can also be used to pass an integer, for example,
so that the normal conversions from a Python object to a C++ integer and
back again are not required.

The reference count of the object being passed is maintained
automatically. There is no need for the emitter of a signal to keep a
reference to the object after the call to [`finished.emit()`{.docutils
.literal .notranslate}]{.pre}, even if a connection is queued.
:::

::: {#connecting-slots-by-name .section}
## Connecting Slots By Name[¶](signals_slots.html#connecting-slots-by-name "Link to this heading"){.headerlink}

PyQt6 supports the [`connectSlotsByName()`{.xref .py .py-meth .docutils
.literal .notranslate}]{.pre} function that is most commonly used by
**pyuic6** generated Python code to automatically connect signals to
slots that conform to a simple naming convention. However, where a class
has overloaded Qt signals (ie. with the same name but with different
arguments) PyQt6 needs additional information in order to automatically
connect the correct signal.

For example the
[QSpinBox](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qspinbox.html){.reference
.external} class has the following signals:

::: {.highlight-default .notranslate}
::: highlight
    void valueChanged(int i);
    void valueChanged(const QString &text);
:::
:::

When the value of the spin box changes both of these signals will be
emitted. If you have implemented a slot called
[`on_spinbox_valueChanged`{.docutils .literal .notranslate}]{.pre}
(which assumes that you have given the QSpinBox instance the name
[`spinbox`{.docutils .literal .notranslate}]{.pre}) then it will be
connected to both variations of the signal. Therefore, when the user
changes the value, your slot will be called twice - once with an integer
argument, and once with a string argument.

The
[pyqtSlot()](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qtcore-module.html#pyqtSlot){.reference
.external} decorator can be used to specify which of the signals should
be connected to the slot.

For example, if you were only interested in the integer variant of the
signal then your slot definition would look like the following:

::: {.highlight-default .notranslate}
::: highlight
    @pyqtSlot(int)
    def on_spinbox_valueChanged(self, i):
        # i will be an integer.
        pass
:::
:::

If you wanted to handle both variants of the signal, but with different
Python methods, then your slot definitions might look like the
following:

::: {.highlight-default .notranslate}
::: highlight
    @pyqtSlot(int, name='on_spinbox_valueChanged')
    def spinbox_int_value(self, i):
        # i will be an integer.
        pass

    @pyqtSlot(str, name='on_spinbox_valueChanged')
    def spinbox_qstring_value(self, s):
        # s will be a Python string object (or a QString if they are enabled).
        pass
:::
:::
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

-   [Support for Signals and Slots](signals_slots.html#){.reference
    .internal}
    -   [Unbound and Bound
        Signals](signals_slots.html#unbound-and-bound-signals){.reference
        .internal}
    -   [Defining New Signals with
        pyqtSignal](signals_slots.html#defining-new-signals-with-pyqtsignal){.reference
        .internal}
        -   [[`PyQt6.QtCore.pyqtSignal()`{.docutils .literal
            .notranslate}]{.pre}](signals_slots.html#PyQt6.QtCore.pyqtSignal){.reference
            .internal}
    -   [Connecting, Disconnecting and Emitting
        Signals](signals_slots.html#connecting-disconnecting-and-emitting-signals){.reference
        .internal}
        -   [[`connect()`{.docutils .literal
            .notranslate}]{.pre}](signals_slots.html#connect){.reference
            .internal}
        -   [[`disconnect()`{.docutils .literal
            .notranslate}]{.pre}](signals_slots.html#disconnect){.reference
            .internal}
        -   [[`emit()`{.docutils .literal
            .notranslate}]{.pre}](signals_slots.html#emit){.reference
            .internal}
    -   [Connecting Signals Using Keyword
        Arguments](signals_slots.html#connecting-signals-using-keyword-arguments){.reference
        .internal}
    -   [The pyqtSlot
        Decorator](signals_slots.html#the-pyqtslot-decorator){.reference
        .internal}
        -   [[`PyQt6.QtCore.pyqtSlot()`{.docutils .literal
            .notranslate}]{.pre}](signals_slots.html#PyQt6.QtCore.pyqtSlot){.reference
            .internal}
    -   [The [`PyQt_PyObject`{.docutils .literal .notranslate}]{.pre}
        Signal Argument
        Type](signals_slots.html#the-pyqt-pyobject-signal-argument-type){.reference
        .internal}
    -   [Connecting Slots By
        Name](signals_slots.html#connecting-slots-by-name){.reference
        .internal}

</div>

<div>

#### Previous topic

[Differences Between PyQt6 and
PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt5_differences.html "previous chapter")

</div>

<div>

#### Next topic

[Support for Qt
Properties](https://www.riverbankcomputing.com/static/Docs/PyQt6/qt_properties.html "next chapter")

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
-   [Support for Signals and Slots](signals_slots.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
