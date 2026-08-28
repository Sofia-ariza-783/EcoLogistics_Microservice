"""Entrypoint to run the EcoLogistics Carbon Tracker Service locally with uvicorn."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
