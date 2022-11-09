# Crop Circle Tracker Server

Default backend server for the [Crop Circle Tracker Plugin](https://github.com/mattjrumble/crop-circle-tracker-plugin).
A FastAPI/Uvicorn webserver with two endpoints, `POST /post/` and `GET /get/`.

* `POST /post/` receives crop circle sightings from the plugin. It expects JSON like `{"world": 514, "location": 3}`.
* `GET /get/` provides the server's best guess of crop circle locations for different worlds. It returns JSON like
  `{"514": {"3": 0.9, "4": 0.1}}` where the outer keys are worlds, the inner keys are locations and the inner values 
  are likelihoods.
* Both endpoints use simple bearer token authentication.
* Sightings are reset every Wednesday 11:30AM UK time to match the weekly game update. The server will return a 503 for all requests made within 30 minutes of this time.
* Server lag is included in calculations, with an estimated rate of 1 minute of lag every day.

### Setup

```
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
