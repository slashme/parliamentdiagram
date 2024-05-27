# Parliament Diagram

The Parliament diagram creator is made for use in Wikipedia, supported by Wikimedia Commons and Wikidata.

![Sample image](src/static/images/AssNat_16_groupes_2022.svg)

You can use the tool at http://parliamentdiagram.toolforge.org/archinputform

## Dependencies

* Requires the parliamentarch, flask and mwoauth Python modules. Install them with `pip install parliamentarch flask mwoauth`.
* Python version 3.11 or later is required.

## Usage

From within the src directory, run `python -m flask run` to start the server locally.
Other ways to run the server are possible, see the Flask documentation.
It is advised to clear the src/static/svgfiles directory regularly.

## OAuth

To enable the feature of uploading the created diagrams to Wikimedia Commons, you need to
[create an OAuth 1.0a consumer](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose/oauth1a)
with the right of editing existing pages, create, edit and move pages, upload new files,
and upload, replace and rename files. The credentials of that consumer then go in the
"oauth_config.toml" file. The callback URL should be "http://<domain>/oauth_callback".

If you want to run the tool without that feature, the toml file should be removed entirely.

## License

This tool is licensed GPL v2, see [LICENSE.md](LICENSE.md).
