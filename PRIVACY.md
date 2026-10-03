# Privacy

Reach Signal does not implement telemetry, advertising, user accounts, tracking pixels, or outbound data uploads. Files are processed by the running Streamlit application. If someone deploys the app, that operator controls infrastructure logs, retention, authentication, backups, and network access and must document those practices separately.

Do not upload personal or confidential data to a deployment you do not control. Prefer de-identified identifiers and apply appropriate access, retention, and disclosure controls.

Inside Signal Hub, Reach Signal runs in Hub mode: uploads stay in the session's memory, the fictional demo is preloaded, and nothing is written to disk.

