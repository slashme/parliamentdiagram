# Parliament Diagram

The Parliament diagram creator is made for use in Wikipedia, supported by Wikimedia Commons and Wikidata.

![Sample image](src/static/images/AssNat_16_groupes_2022.svg)

You can use the tool at http://parliamentdiagram.toolforge.org/archinputform

## Dependencies

* Requires the parliamentarch and flask Python modules. Install them with `pip install parliamentarch flask`.
* Python version 3.12 or later is required (due to the parliamentarch module).

## Usage

From within the src directory, run `python -m flask run` to start the server locally.
Other ways to run the server are possible, see the Flask documentation.
It is advised to clear the src/static/svgfiles directory regularly.

## License

This tool is licensed GPL v2, see [LICENSE.md](LICENSE.md).
