Generate structured output with the Gemini API

Python JavaScript Go REST

Gemini generates unstructured text by default, but some applications require structured text. For these use cases, you can constrain Gemini to respond with JSON, a structured data format suitable for automated processing. You can also constrain the model to respond with one of the options specified in an enum.

Here are a few use cases that might require structured output from the model:

Build a database of companies by pulling company information out of newspaper articles.
Pull standardized information out of resumes.
Extract ingredients from recipes and display a link to a grocery website for each ingredient.
In your prompt, you can ask Gemini to produce JSON-formatted output, but note that the model is not guaranteed to produce JSON and nothing but JSON. For a more deterministic response, you can pass a specific JSON schema in a responseSchema field so that Gemini always responds with an expected structure. To learn more about working with schemas, see More about JSON schemas.

This guide shows you how to generate JSON using the generateContent method through the SDK of your choice or using the REST API directly. The examples show text-only input, although Gemini can also produce JSON responses to multimodal requests that include images, videos, and audio.

Generate JSON
When the model is configured to output JSON, it responds to any prompt with JSON-formatted output.

You can control the structure of the JSON response by supplying a schema. There are two ways to supply a schema to the model:

As text in the prompt
As a structured schema supplied through model configuration
Supply a schema as text in the prompt
The following example prompts the model to return cookie recipes in a specific JSON format.

Since the model gets the format specification from text in the prompt, you may have some flexibility in how you represent the specification. Any reasonable format for representing a JSON schema may work.

from google import genai

prompt = """List a few popular cookie recipes in JSON format.

Use this JSON schema:

Recipe = {'recipe_name': str, 'ingredients': list[str]}
Return: list[Recipe]"""

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
model='gemini-2.0-flash',
contents=prompt,
)

# Use the response as a JSON string.

print(response.text)
The output might look like this:

[
{
"recipe_name": "Chocolate Chip Cookies",
"ingredients": [
"2 1/4 cups all-purpose flour",
"1 teaspoon baking soda",
"1 teaspoon salt",
"1 cup (2 sticks) unsalted butter, softened",
"3/4 cup granulated sugar",
"3/4 cup packed brown sugar",
"1 teaspoon vanilla extract",
"2 large eggs",
"2 cups chocolate chips"
]
},
...
]
Supply a schema through model configuration
The following example does the following:

Instantiates a model configured through a schema to respond with JSON.
Prompts the model to return cookie recipes.
This more formal method for declaring the JSON schema gives you more precise control than relying just on text in the prompt.

Important: When you're working with JSON schemas in the Gemini API, the order of properties matters. For more information, see Property ordering.

from google import genai
from pydantic import BaseModel

class Recipe(BaseModel):
recipe_name: str
ingredients: list[str]

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
model='gemini-2.0-flash',
contents='List a few popular cookie recipes. Be sure to include the amounts of ingredients.',
config={
'response_mime_type': 'application/json',
'response_schema': list[Recipe],
},
)

# Use the response as a JSON string.

print(response.text)

# Use instantiated objects.

my_recipes: list[Recipe] = response.parsed
The output might look like this:

[
{
"recipe_name": "Chocolate Chip Cookies",
"ingredients": [
"1 cup (2 sticks) unsalted butter, softened",
"3/4 cup granulated sugar",
"3/4 cup packed brown sugar",
"1 teaspoon vanilla extract",
"2 large eggs",
"2 1/4 cups all-purpose flour",
"1 teaspoon baking soda",
"1 teaspoon salt",
"2 cups chocolate chips"
]
},
...
]
Note: Pydantic validators are not yet supported. If a pydantic.ValidationError occurs, it is suppressed, and .parsed may be empty/null.
Schema Definition Syntax
Specify the schema for the JSON response in the response_schema property of your model configuration. The value of response_schema must be a either:

A type, as you would use in a type annotation. See the Python typing module.
An instance of genai.types.Schema.
The dict equivalent of genai.types.Schema.
Define a Schema with a Type
The easiest way to define a schema is with a direct type. This is the approach used in the preceding example:

config={'response_mime_type': 'application/json',
'response_schema': list[Recipe]}
The Gemini API Python client library supports schemas defined with the following types (where AllowedType is any allowed type):

int
float
bool
str
list[AllowedType]
For structured types:
dict[str, AllowedType]. This annotation declares all dict values to be the same type, but doesn't specify what keys should be included.
User-defined Pydantic models. This approach lets you specify the key names and define different types for the values associated with each of the keys, including nested structures.
Use an enum to constrain output
In some cases you might want the model to choose a single option from a list of options. To implement this behavior, you can pass an enum in your schema. You can use an enum option anywhere you could use a str in the response_schema, because an enum is a list of strings. Like a JSON schema, an enum lets you constrain model output to meet the requirements of your application.

For example, assume that you're developing an application to classify musical instruments into one of five categories: "Percussion", "String", "Woodwind", "Brass", or ""Keyboard"". You could create an enum to help with this task.

In the following example, you pass the enum class Instrument as the response_schema, and the model should choose the most appropriate enum option.

from google import genai
import enum

class Instrument(enum.Enum):
PERCUSSION = "Percussion"
STRING = "String"
WOODWIND = "Woodwind"
BRASS = "Brass"
KEYBOARD = "Keyboard"

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
model='gemini-2.0-flash',
contents='What type of instrument is an oboe?',
config={
'response_mime_type': 'text/x.enum',
'response_schema': Instrument,
},
)

print(response.text)

# Woodwind

The Python SDK will translate the type declarations for the API. However, the API accepts a subset of the OpenAPI 3.0 schema (Schema). You can also pass the schema as JSON:

from google import genai

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
model='gemini-2.0-flash',
contents='What type of instrument is an oboe?',
config={
'response_mime_type': 'text/x.enum',
'response_schema': {
"type": "STRING",
"enum": ["Percussion", "String", "Woodwind", "Brass", "Keyboard"],
},
},
)

print(response.text)

# Woodwind

Beyond basic multiple choice problems, you can use an enum anywhere in a schema for JSON or function calling. For example, you could ask the model for a list of recipe titles and use a Grade enum to give each title a popularity grade:

from google import genai

import enum
from pydantic import BaseModel

class Grade(enum.Enum):
A_PLUS = "a+"
A = "a"
B = "b"
C = "c"
D = "d"
F = "f"

class Recipe(BaseModel):
recipe_name: str
rating: Grade

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
model='gemini-2.0-flash',
contents='List 10 home-baked cookies and give them grades based on tastiness.',
config={
'response_mime_type': 'application/json',
'response_schema': list[Recipe],
},
)

print(response.text)

# [{"rating": "a+", "recipe_name": "Classic Chocolate Chip Cookies"}, ...]

More about JSON schemas
When you configure the model to return a JSON response, you can use a Schema object to define the shape of the JSON data. The Schema represents a select subset of the OpenAPI 3.0 Schema object.

Here's a pseudo-JSON representation of all the Schema fields:

{
"type": enum (Type),
"format": string,
"description": string,
"nullable": boolean,
"enum": [
string
],
"maxItems": string,
"minItems": string,
"properties": {
string: {
object (Schema)
},
...
},
"required": [
string
],
"propertyOrdering": [
string
],
"items": {
object (Schema)
}
}
The Type of the schema must be one of the OpenAPI Data Types. Only a subset of fields is valid for each Type. The following list maps each Type to valid fields for that type:

string -> enum, format
integer -> format
number -> format
boolean
array -> minItems, maxItems, items
object -> properties, required, propertyOrdering, nullable
Here are some example schemas showing valid type-and-field combinations:

{ "type": "string", "enum": ["a", "b", "c"] }

{ "type": "string", "format": "date-time" }

{ "type": "integer", "format": "int64" }

{ "type": "number", "format": "double" }

{ "type": "boolean" }

{ "type": "array", "minItems": 3, "maxItems": 3, "items": { "type": ... } }

{ "type": "object",
"properties": {
"a": { "type": ... },
"b": { "type": ... },
"c": { "type": ... }
},
"nullable": true,
"required": ["c"],
"propertyOrdering": ["c", "b", "a"]
}
For complete documentation of the Schema fields as they're used in the Gemini API, see the Schema reference.

Property ordering
When you're working with JSON schemas in the Gemini API, the order of properties is important. By default, the API orders properties alphabetically and does not preserve the order in which the properties are defined (although the Google Gen AI SDKs may preserve this order). If you're providing examples to the model with a schema configured, and the property ordering of the examples is not consistent with the property ordering of the schema, the output could be rambling or unexpected.

To ensure a consistent, predictable ordering of properties, you can use the optional propertyOrdering[] field.

"propertyOrdering": ["recipe_name", "ingredients"]
propertyOrdering[] – not a standard field in the OpenAPI specification – is an array of strings used to determine the order of properties in the response. By specifying the order of properties and then providing examples with properties in that same order, you can potentially improve the quality of results.

Key Point: To improve results when you're using a JSON schema, set propertyOrdering[] and provide examples with a matching property ordering.
