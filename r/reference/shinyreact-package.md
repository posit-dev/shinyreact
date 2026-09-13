# shinyreact: Client-Side 'React' Interface for 'Shiny'

Server-side plumbing for the 'ui.tsx' pattern in 'Shiny': the user
interface is defined in a client 'React' (<https://react.dev/>) bundle,
and the 'Shiny' server contains only reactive computation. Provides page
builders that discover and serve the client bundle, a render function
that publishes any JSON-serializable value to the client, and custom
messages to 'React' components. Ships no user interface components, so
the app author owns the whole front end. The 'React' runtime and the
client hooks are bundled, so no JavaScript build step is required to get
started.

## See also

Useful links:

- <https://posit-dev.github.io/shinyreact/r/>

- <https://github.com/posit-dev/shinyreact>

- Report bugs at <https://github.com/posit-dev/shinyreact/issues>

## Author

**Maintainer**: Barret Schloerke <barret@posit.co>
([ORCID](https://orcid.org/0000-0001-9986-114X))

Authors:

- Barret Schloerke <barret@posit.co>
  ([ORCID](https://orcid.org/0000-0001-9986-114X))

Other contributors:

- Winston Chang <winston@posit.co>
  ([ORCID](https://orcid.org/0000-0002-1576-2126)) \[contributor\]

- Garrick Aden-Buie <garrick@adenbuie.com>
  ([ORCID](https://orcid.org/0000-0002-7111-0077)) \[contributor\]

- Carson Sievert <carson@posit.co>
  ([ORCID](https://orcid.org/0000-0002-4958-2844)) \[contributor\]

- Posit Software, PBC ([ROR](https://ror.org/03wc8by49)) \[copyright
  holder, funder\]

- Meta Platforms, Inc. ('React' and 'ReactDOM', bundled in
  inst/lib/shiny/shinyreact.js) \[copyright holder\]
