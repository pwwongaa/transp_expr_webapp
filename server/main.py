import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path  # dir path
from typing import List  # List, response model
from urllib.parse import quote

from fastapi import (BackgroundTasks, FastAPI, File, HTTPException, Query,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

#? FASTAPI Object
app = FastAPI()

# add CORS middleware - allow react front end access

#* need to allow picture CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", ""],  # React dev server port
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


#!CHANGE TO AWS EC2 hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pwwongaa.github.io",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#? essential dirs
# UPLOAD_DIR = Path("./data") #upload dir
UPLOAD_DIR = Path("/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/data") #!AWS EC2
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) #auto make a dir if not exist
DATA_DIR = UPLOAD_DIR

# RESULT_DIR = Path("./results")
RESULT_DIR = Path("/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/results") #!AWS EC2
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# mount to drive
# after you create app = FastAPI()
# then the files would be availabel in React FE
app.mount(
  "/results",
  StaticFiles(directory=str(RESULT_DIR)),
  name="results"
)

#file download if necessary, or jsut use webbrowser download

#? Routes - (modularised in routes.py later//)
#i. root page
@app.get("/")
def read_root():
    return {"msg": "Backend working"}

#ii. uplaod page - #!DONE
@app.post("/upload")
async def upload_two_files(
    expression_matrix: UploadFile = File(...), #two file uploading entry form react front end
    covariate_table: UploadFile = File(...)
):
    # print("Working dir:", os.getcwd())
    # print("Saving to:", UPLOAD_DIR.resolve())
    #i. store the expression_matrix, add a tag to uploaded 
    expr_name = Path(expression_matrix.filename)
    expr_saved_name = expr_name.stem + "__expr" + expr_name.suffix
    save_expr_path = UPLOAD_DIR / expr_saved_name
    with save_expr_path.open("wb") as buf1:
        shutil.copyfileobj(expression_matrix.file, buf1)

    #ii. store the covariate_table, add a tag to uploaded 
    cov_name = Path(covariate_table.filename)
    cov_saved_name = cov_name.stem + "__cov" + cov_name.suffix
    save_cov_path = UPLOAD_DIR / cov_saved_name
    with save_cov_path.open("wb") as buf2:
        shutil.copyfileobj(covariate_table.file, buf2)

    return {
        "expression_matrix": expression_matrix.filename,
        "covariate_table": covariate_table.filename
    }


#result route: **when enter Home: perform reset of all data/ and result/
##then trigger this when React FE return
@app.post("/reset")
async def reset_pipeline():
    try:
        # Remove and recreate data directory: data/
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
        DATA_DIR.mkdir()

        # Remove and recreate results directory: results/
        if RESULT_DIR.exists():
            shutil.rmtree(RESULT_DIR)
        RESULT_DIR.mkdir()
        return {"reset": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


FLAG_FILE = RESULT_DIR / 'completed.flag'
# OUTPUT_PNG  = RESULT_DIR / 'mean_expression.png'

#? Run and Status listening - pipeline
# shared status
status_store = {
    "state": "idle",      # idle / processing / done / error
    "error": None,         #error state
}

class RunResponse(BaseModel):
    success: bool

class StatusResponse(BaseModel):
    status: str
    error: str | None = None


#pipeline function
def pipeline_job():
    try:
        status_store["state"] = "processing"
        status_store["error"] = None

        CONDA_PYTHON = "/home/ubuntu/miniforge3/envs/transcp_webapp/bin/python" #conda env python

        #! pipeline execution
        time.sleep(1)   
        # subprocess.run(
        #     # [sys.executable, "pipeline/runner.py"],
        #     [CONDA_PYTHON, "/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/pipeline/runner.py"],
        #     # cwd=".",  # ensure runner.py sees the data folder
        #     cwd="/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/",
        #     check=True,
        #     capture_output=True,
        #     text=True)
        subprocess.run(
        [
            "systemd-run", "--scope", "-p", "MemoryMax=3G",
            CONDA_PYTHON,
            "/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/pipeline/runner.py"
        ],
        cwd="/home/ubuntu/hosting_transcp_webapp/transp_expr_webapp/server/",
        check=True,
        capture_output=True,
        text=True
        )
        time.sleep(1)   
        # If you catch exceptions in here, set error below
        # -------------------------------------------

        #? state change once finished
        status_store["state"] = "done"
    #error
    except Exception as e:
        status_store["state"] = "error"
        status_store["error"] = str(e)


#ii. Run - pipeline execution
# @app.post("/run")
# async def run_pipeline():
#     try:
        #pass
#         return {"success": True}
#     except subprocess.CalledProcessError as e:
#         print("Pipeline stderr:", e.stderr, file=sys.stderr)
#         raise HTTPException(500, detail=e.stderr or e.stdout)

@app.post("/run", response_model=RunResponse) #Add RunResponse
async def run_pipeline(background_tasks: BackgroundTasks): #Move to Background Tasks - prevent oocupying the HTTP POST request until pipeline finished*
    # Start the pipelien in the bkgd
    background_tasks.add_task(pipeline_job)
    return {"success": True} #return a True --> initiate the navigation

#iii. analysis page
@app.get("/analysis", response_model=StatusResponse)
async def get_status():
    # Called by your React poll every 5s
    ##Pipeline Listener: StatusResponse -> once the pieplien finished, return state
    return {
        "status": status_store["state"],
        "error": status_store["error"]
    }

#iv. Result viewing/feedback from pipeline ,py
@app.get("/result-flag")
def get_result(filename: str):
    #the flag file for noticing the finish of pipeline analysis
    flag_file = RESULT_DIR / 'completed.flag'
    if flag_file.exists():
        content = flag_file.read_text()
        return {"filename": filename, "content": content}
    else:
        return {"error": "Result not found"}

#handle picture 
@app.get("/result-files", response_model=List[str]) #respone you the list
def list_results(extension: str = "png"):
    return [f.name for f in RESULT_DIR.glob(f"*.{extension}")]

#health check route
@app.get("/health")
def health():
    return {"status": "ok"}