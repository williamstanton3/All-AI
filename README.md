# All-AI
A website where a user can enter a prompt and simultaneously get responses from multiple leading LLMs and compare their responses side by side.


### Setup
* Python

    The following Python packages are required:

    <code>SQLAlchemy Flask Flask-SQLAlchemy Flask-Login openai google-genai xai-sdk anthropic</code>


* Typescript compiler (any recent version should be sufficient)

    Note that this is not necessary unless you want to modify the frontend, as the project already contains compiled Javascript files.

### Running

* To run the backend server in debug mode, simply run 
<code>python -m flask --app app run --debug</code>.