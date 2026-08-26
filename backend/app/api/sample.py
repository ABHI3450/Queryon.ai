"""
Sample File API Router
======================
Allows downloading the sample CSV dataset directly from the app.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api", tags=["sample"])

@router.get("/sample-data", summary="Download sample sales CSV dataset")
async def download_sample_data():
    """
    Serves the sample_data/sales_data.csv file for immediate testing.
    """
    # Look for sample_data folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "sample_data", "sales_data.csv"))

    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample dataset file not found")

    return FileResponse(
        path=sample_path,
        media_type="text/csv",
        filename="sample_sales_data.csv",
    )
