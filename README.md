# Crop Circle Tracker Server

Backend server for the [Crop Circle Tracker Plugin](https://github.com/mattjrumble/crop-circle-tracker-plugin).
A FastAPI/Uvicorn webserver with two endpoints, `POST /` and `GET /`.

* `POST /` receives crop circle sightings from the plugin. It expects JSON like `{"world": 514, "location": 3}`.
* `GET /` provides the server's best guess of crop circle locations for different worlds. It returns JSON like
  `{"514": {"3": 0.9, "4": 0.1}}` where the outer keys are worlds, the inner keys are locations and the inner values 
  are likelihoods.
* Both endpoints use simple bearer token authentication.
