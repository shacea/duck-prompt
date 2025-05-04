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
-   [Support for Cooperative Multi-inheritance](multiinheritance.html)
:::

::: document
::: documentwrapper
::: bodywrapper
::: {.body role="main"}
::: {#support-for-cooperative-multi-inheritance .section}
[]{#ref-cooperative-multiinheritance}

# Support for Cooperative Multi-inheritance[¶](multiinheritance.html#support-for-cooperative-multi-inheritance "Link to this heading"){.headerlink}

::: {.admonition .note}
Note

This section is not about sub-classing from more that one Qt class.
:::

Cooperative multi-inheritance is a technique for implementing classes
that inherit multiple super-classes - typically a main super-class and
one or more mixin classes that add additional behaviour. It makes it
easy to add new mixins at a later date to further extend the behavior,
without needing to change either the implementation of the class or any
existing code that creates an instance of the class.

The technique requires that all the super-class's [`__init__`{.docutils
.literal .notranslate}]{.pre} methods follow the same pattern in the way
that they handle unrecognised keyword arguments and use
[`super()`{.docutils .literal .notranslate}]{.pre} to invoke their own
super-class's [`__init__`{.docutils .literal .notranslate}]{.pre}
methods.

PyQt6's classes follow this pattern.

See Raymond Hettinger's [Python's super() considered
super!](http://rhettinger.wordpress.com/2011/05/26/super-considered-super/){.reference
.external} blog post for some more background on the subject.

As an example, let's say we have a class that represents a person, and
that a person has a name. The following might be an initial
implementation:

::: {.highlight-default .notranslate}
::: highlight
    class Person(QObject):
        def __init__(self, name, parent=None)
            QObject.__init__(self, parent)

            self.name = name
:::
:::

An instance would normally be created in one of the following ways:

::: {.highlight-default .notranslate}
::: highlight
    person = Person("Joe")
    person = Person("Joe", some_parent)
:::
:::

This approach has some limitations:

-   Only a sub-set of the
    [QObject](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qobject.html){.reference
    .external} API is exposed. For example you cannot set the value of a
    Qt property or connect a signal by passing appropriate keyword
    arguments to [`Person.__init__`{.docutils .literal
    .notranslate}]{.pre}.

-   Adding another class to [`Person`{.docutils .literal
    .notranslate}]{.pre}'s list of super-classes means that its
    [`__init__`{.docutils .literal .notranslate}]{.pre} implementation
    needs to be changed. If the new mixin takes non-optional arguments
    then every call to create a [`Person`{.docutils .literal
    .notranslate}]{.pre} instance will need changing.

Consider this alternative implementation:

::: {.highlight-default .notranslate}
::: highlight
    class Person(QObject):
        def __init__(self, name, **kwds):
            super().__init__(**kwds)

            self.name = name
:::
:::

The difference is that we only handle arguments that are used by the
[`Person`{.docutils .literal .notranslate}]{.pre} class itself and we
punt all the other arguments to the super-classes by calling
[`super()`{.docutils .literal .notranslate}]{.pre}.

With this implementation an instance would normally be created in one of
the following ways:

::: {.highlight-default .notranslate}
::: highlight
    person = Person("Joe")
    person = Person("Joe", parent=some_parent)
:::
:::

Here the difference is that we are using keyword arguments to specify
any arguments that are not handled by the [`Person`{.docutils .literal
.notranslate}]{.pre} class itself. Note that we could use keyword
arguments for all arguments - whether or not you do so is down to
personal choice.

The limitations of the first implementation no longer apply. For
example, without any further changes we can also do this:

::: {.highlight-default .notranslate}
::: highlight
    person = Person("Joe", destroyed=some_callable)
:::
:::

Let's say we now want to extend the behaviour of the [`Person`{.docutils
.literal .notranslate}]{.pre} class by adding a mixin that handles a
person's age. The implementation of the mixin would be as follows:

::: {.highlight-default .notranslate}
::: highlight
    class Age(object):
        def __init__(self, age=0, **kwds):
            super().__init__(**kwds)

            self.age = age
:::
:::

This follows a similar pattern to our [`Person`{.docutils .literal
.notranslate}]{.pre} implementation, but notice that we have provided
the [`age`{.docutils .literal .notranslate}]{.pre} argument with a
default value.

The following is our new [`Person`{.docutils .literal
.notranslate}]{.pre} implementation:

::: {.highlight-default .notranslate}
::: highlight
    class Person(QObject, Age):
        def __init__(self, name, **kwds):
            super().__init__(**kwds)

            self.name = name
:::
:::

The only change we have had to make is to add [`Age`{.docutils .literal
.notranslate}]{.pre} to [`Person`{.docutils .literal
.notranslate}]{.pre}'s list of super-classes. More importantly we do not
need to change any call to create a [`Person`{.docutils .literal
.notranslate}]{.pre} instance.

If we do want to create a [`Person`{.docutils .literal
.notranslate}]{.pre} instance with a non-default age then we simply pass
it as a keyword argument as follows:

::: {.highlight-default .notranslate}
::: highlight
    person = Person("Joe", age=38)
:::
:::

This technique increases the use of keyword arguments - while this means
a bit more typing, it significantly increases the readability of
application code.
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

[Integrating Python and
QML](https://www.riverbankcomputing.com/static/Docs/PyQt6/qml.html "previous chapter")

</div>

<div>

#### Next topic

[Things to be Aware
Of](https://www.riverbankcomputing.com/static/Docs/PyQt6/gotchas.html "next chapter")

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
-   [Support for Cooperative Multi-inheritance](multiinheritance.html)
:::

::: {.footer role="contentinfo"}
© Copyright 2025, Riverbank Computing Limited, The Qt Company. Created
using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
:::
