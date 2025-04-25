[Skip to content](https://langchain-ai.github.io/langgraph/reference/channels/#channels)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/reference/channels.md "Edit this page")

# Channels [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#channels "Permanent link")

Classes:

- **`BaseChannel`**
–



## `` BaseChannel [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel "Permanent link")

Bases: `Generic[Value, Update, C]`, `ABC`

Methods:

- **`copy`**
–



Return a copy of the channel.

- **`checkpoint`**
–



Return a serializable representation of the channel's current state.

- **`from_checkpoint`**
–



Return a new identical channel, optionally initialized from a checkpoint.

- **`update`**
–



Update the channel's value with the given sequence of updates.

- **`get`**
–



Return the current value of the channel.

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`is_available`**
–



Return True if the channel is available (not empty), False otherwise.


Attributes:

- **`ValueType`**
( `Any`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `Any`)
–



The type of the update received by the channel.


### `` ValueType`abstractmethod``property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.ValueType "Permanent link")

```md-code__content
ValueType: Any

```

The type of the value stored in the channel.

### `` UpdateType`abstractmethod``property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.UpdateType "Permanent link")

```md-code__content
UpdateType: Any

```

The type of the update received by the channel.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.
By default, delegates to checkpoint() and from\_checkpoint().
Subclasses can override this method with a more efficient implementation.

### `` checkpoint [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.checkpoint "Permanent link")

```md-code__content
checkpoint() -> C

```

Return a serializable representation of the channel's current state.
Raises EmptyChannelError if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `` from\_checkpoint`abstractmethod`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.from_checkpoint "Permanent link")

```md-code__content
from_checkpoint(checkpoint: C) -> Self

```

Return a new identical channel, optionally initialized from a checkpoint.
If the checkpoint contains complex data structures, they should be copied.

### `` update`abstractmethod`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.update "Permanent link")

```md-code__content
update(values: Sequence[Update]) -> bool

```

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.
If there are no updates, it is called with an empty sequence.
Raises InvalidUpdateError if the sequence of updates is invalid.
Returns True if the channel was updated, False otherwise.

### `` get`abstractmethod`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.get "Permanent link")

```md-code__content
get() -> Value

```

Return the current value of the channel.

Raises EmptyChannelError if the channel is empty (never updated yet).

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` is\_available [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.base.BaseChannel.is_available "Permanent link")

```md-code__content
is_available() -> bool

```

Return True if the channel is available (not empty), False otherwise.
Subclasses should override this method to provide a more efficient
implementation than calling get() and catching EmptyChannelError.

Classes:

- **`Topic`**
–



A configurable PubSub Topic.

- **`LastValue`**
–



Stores the last value received, can receive at most one value per step.

- **`EphemeralValue`**
–



Stores the value received in the step immediately preceding, clears after.

- **`BinaryOperatorAggregate`**
–



Stores the result of applying a binary operator to the current value and each new value.

- **`AnyValue`**
–



Stores the last value received, assumes that if multiple values are


## `` Topic [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.Topic "Permanent link")

Bases: `Generic[Value]`, `BaseChannel[Sequence[Value], Union[Value, list[Value]], list[Value]]`

A configurable PubSub Topic.

Parameters:

- **`typ`**
( `type[Value]`)
–



The type of the value stored in the channel.

- **`accumulate`**
( `bool`, default:
`False`
)
–



Whether to accumulate values across steps. If False, the channel will be emptied after each step.


Methods:

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`copy`**
–



Return a copy of the channel.


Attributes:

- **`ValueType`**
( `Any`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `Any`)
–



The type of the update received by the channel.


### `` ValueType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.Topic.ValueType "Permanent link")

```md-code__content
ValueType: Any

```

The type of the value stored in the channel.

### `` UpdateType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.Topic.UpdateType "Permanent link")

```md-code__content
UpdateType: Any

```

The type of the update received by the channel.

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.Topic.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.Topic.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.

## `` LastValue [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.LastValue "Permanent link")

Bases: `Generic[Value]`, `BaseChannel[Value, Value, Value]`

Stores the last value received, can receive at most one value per step.

Methods:

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`copy`**
–



Return a copy of the channel.


Attributes:

- **`ValueType`**
( `type[Value]`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `type[Value]`)
–



The type of the update received by the channel.


### `` ValueType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.LastValue.ValueType "Permanent link")

```md-code__content
ValueType: type[Value]

```

The type of the value stored in the channel.

### `` UpdateType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.LastValue.UpdateType "Permanent link")

```md-code__content
UpdateType: type[Value]

```

The type of the update received by the channel.

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.LastValue.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.LastValue.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.

## `` EphemeralValue [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.EphemeralValue "Permanent link")

Bases: `Generic[Value]`, `BaseChannel[Value, Value, Value]`

Stores the value received in the step immediately preceding, clears after.

Methods:

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`copy`**
–



Return a copy of the channel.


Attributes:

- **`ValueType`**
( `type[Value]`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `type[Value]`)
–



The type of the update received by the channel.


### `` ValueType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.EphemeralValue.ValueType "Permanent link")

```md-code__content
ValueType: type[Value]

```

The type of the value stored in the channel.

### `` UpdateType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.EphemeralValue.UpdateType "Permanent link")

```md-code__content
UpdateType: type[Value]

```

The type of the update received by the channel.

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.EphemeralValue.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.EphemeralValue.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.

## `` BinaryOperatorAggregate [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.BinaryOperatorAggregate "Permanent link")

Bases: `Generic[Value]`, `BaseChannel[Value, Value, Value]`

Stores the result of applying a binary operator to the current value and each new value.

```md-code__content
import operator

total = Channels.BinaryOperatorAggregate(int, operator.add)

```

Methods:

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`copy`**
–



Return a copy of the channel.


Attributes:

- **`ValueType`**
( `type[Value]`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `type[Value]`)
–



The type of the update received by the channel.


### `` ValueType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.BinaryOperatorAggregate.ValueType "Permanent link")

```md-code__content
ValueType: type[Value]

```

The type of the value stored in the channel.

### `` UpdateType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.BinaryOperatorAggregate.UpdateType "Permanent link")

```md-code__content
UpdateType: type[Value]

```

The type of the update received by the channel.

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.BinaryOperatorAggregate.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.BinaryOperatorAggregate.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.

## `` AnyValue [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.AnyValue "Permanent link")

Bases: `Generic[Value]`, `BaseChannel[Value, Value, Value]`

Stores the last value received, assumes that if multiple values are
received, they are all equal.

Methods:

- **`consume`**
–



Mark the current value of the channel as consumed. By default, no-op.

- **`copy`**
–



Return a copy of the channel.


Attributes:

- **`ValueType`**
( `type[Value]`)
–



The type of the value stored in the channel.

- **`UpdateType`**
( `type[Value]`)
–



The type of the update received by the channel.


### `` ValueType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.AnyValue.ValueType "Permanent link")

```md-code__content
ValueType: type[Value]

```

The type of the value stored in the channel.

### `` UpdateType`property`[¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.AnyValue.UpdateType "Permanent link")

```md-code__content
UpdateType: type[Value]

```

The type of the update received by the channel.

### `` consume [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.AnyValue.consume "Permanent link")

```md-code__content
consume() -> bool

```

Mark the current value of the channel as consumed. By default, no-op.
This is called by Pregel before the start of the next step, for all
channels that triggered a node. If the channel was updated, return True.

### `` copy [¶](https://langchain-ai.github.io/langgraph/reference/channels/\#langgraph.channels.AnyValue.copy "Permanent link")

```md-code__content
copy() -> Self

```

Return a copy of the channel.

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/2345)

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/2345)

#### ·

#### 1 reply

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@lakshaytalkstomachines](https://avatars.githubusercontent.com/u/38259381?u=c32bd533ee3f00d899ec906c6878f3a5a4fd91d5&v=4)lakshaytalkstomachines](https://github.com/lakshaytalkstomachines) [Nov 5, 2024](https://github.com/langchain-ai/langgraph/discussions/2345#discussioncomment-11159968)

What is essentially a channel though?

1

1 reply

[![@prashand](https://avatars.githubusercontent.com/u/5242391?v=4)](https://github.com/prashand)

[prashand](https://github.com/prashand) [Nov 23, 2024](https://github.com/langchain-ai/langgraph/discussions/2345#discussioncomment-11355979)

Essentially, a channel is a single key in the schema(s) of the graph state.

👍1

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Freference%2Fchannels%2F)