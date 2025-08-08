
# Import FastAPI framework and HTTPException for error handling
from fastapi import FastAPI, HTTPException
# Import the list_vms function from our own libvirt_client module
from libvirt_client import list_vms


# Create the FastAPI application instance
app = FastAPI()


# Root endpoint: returns a simple message to show the API is running
@app.get("/")
def root():
    return {"message": "It works!"}


# Health check endpoint: returns a status message
@app.get("/status")
def status():
    return {"status": "healthy"}


# Endpoint to list all virtual machines
# Calls our list_vms() function to get VM info from libvirt
@app.get("/vms")
def get_vms():
    try:
        vms = list_vms()  # defaults to qemu:///system
        # Return the number of VMs and their details as JSON
        return {"count": len(vms), "vms": vms}
    except Exception as e:
        # If something goes wrong, return a 500 error with the error message
        raise HTTPException(status_code=500, detail=str(e))

