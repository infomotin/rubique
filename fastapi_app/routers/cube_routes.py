"""
CubePermutation AI - FastAPI Cube Processing Router
===================================================
Handles core speedcubing & group theory computational pipelines:
- WCA Scramble Generation
- Kociemba Two-Phase Minimal Step Solving with Step Explanations
- OpenCV Computer Vision Facelet Extraction (CLAHE + HSV Segmentation)
- Solve History Tracking (MySQL Solves Table)
- Pattern Studio Algorithm Library
"""

import base64
import random
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import solver_engine
import pattern_library
from models.solve_model import SolveModel
from controllers.api_controller import (
    process_cube_image, SAMPLE_PRESETS, generate_annotated_sample_image
)
from fastapi_app.dependencies import get_current_user, get_optional_current_user

router = APIRouter(tags=["Cube & Vision Processing"])


class SolveRequest(BaseModel):
    facelet_string: Optional[str] = None
    cube_state: Optional[str] = None
    custom_moves: Optional[str] = None


class ScanPresetRequest(BaseModel):
    sample_id: Optional[str] = None
    image_base64: Optional[str] = None


@router.get("/api/scramble")
@router.get("/api/v1/cube/scramble")
async def get_scramble():
    """Generates random WCA scramble and preliminary solution"""
    faces = ['U', 'D', 'F', 'B', 'L', 'R']
    suffixes = ['', "'", '2']
    scramble_moves = []
    last_f, second_last_f = None, None

    for _ in range(random.randint(14, 18)):
        valid = [f for f in faces if f != last_f and f != second_last_f]
        f = random.choice(valid)
        scramble_moves.append(f + random.choice(suffixes))
        second_last_f = last_f
        last_f = f

    scramble_str = " ".join(scramble_moves)
    solution_str = solver_engine.solve_cube(scramble_str)

    return {
        "scramble": scramble_str,
        "solution": solution_str,
        "move_count": len(solution_str.split()) if solution_str else 0
    }


@router.post("/api/solve")
@router.post("/api/v1/cube/solve")
async def solve_cube(
    req: SolveRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Solves current cube sequence or 54-facelet state with optimal Two-Phase solver
    and move-by-move explanations.
    Logs solve to MySQL when authenticated.
    """
    facelet_string = req.facelet_string or req.cube_state
    custom_moves = req.custom_moves

    if facelet_string is not None and str(facelet_string).strip() != '':
        facelet_string = str(facelet_string).strip()
        if len(facelet_string) != 54:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Facelet string must be exactly 54 characters (received {len(facelet_string)})."
            )
        target_state = facelet_string
    else:
        target_state = (custom_moves or "").strip()

    result = solver_engine.solve_state(target_state)
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"]
        )

    solution = result["solution"]
    moves_list = result["moves"]
    steps_data = solver_engine.generate_step_explanations(moves_list)

    # Record to MySQL solve history if user is authenticated
    if current_user and moves_list:
        recorded_input = facelet_string or custom_moves or "Cube State"
        SolveModel.record_solve(
            current_user["id"],
            recorded_input[:120],
            solution,
            len(moves_list)
        )

    return {
        "success": True,
        "solution": solution,
        "moves": moves_list,
        "steps": steps_data,
        "move_count": len(moves_list),
        "engine": result.get("engine", "two_phase"),
        "method": "Two-Phase Kociemba Minimal Step Solver"
    }


@router.post("/api/scan-image")
@router.post("/api/v1/cube/scan-image")
async def scan_image(
    image: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None)
):
    """
    OpenCV facelet segmentation scanner endpoint supporting:
    - Multipart file upload (camera / gallery)
    - Base64 encoded JPEG/PNG payload
    - Sample presets (sample_u, sample_f, sample_r, sample_solved)
    """
    # 1. Preset check
    if sample_id and sample_id in SAMPLE_PRESETS:
        grid = SAMPLE_PRESETS[sample_id]
        preview = generate_annotated_sample_image(grid)
        return {
            "success": True,
            "face_grid": grid,
            "annotated_image": preview,
            "center_color": grid[1][1]
        }

    # 2. File upload check
    if image is not None:
        try:
            content = await image.read()
            res = process_cube_image(content)
            return {
                "success": True,
                "face_grid": res["face_grid"],
                "annotated_image": res["annotated_image"],
                "center_color": res["center_color"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image processing error: {str(e)}"
            )

    # 3. Base64 payload check
    if image_base64:
        b64_str = image_base64
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        try:
            raw = base64.b64decode(b64_str)
            res = process_cube_image(raw)
            return {
                "success": True,
                "face_grid": res["face_grid"],
                "annotated_image": res["annotated_image"],
                "center_color": res["center_color"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image base64 decoding error: {str(e)}"
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No image file, base64 payload, or sample preset provided."
    )


@router.post("/api/v1/cube/scan-json")
async def scan_json_payload(req: ScanPresetRequest):
    """JSON variant for scanning base64 or sample presets"""
    if req.sample_id and req.sample_id in SAMPLE_PRESETS:
        grid = SAMPLE_PRESETS[req.sample_id]
        preview = generate_annotated_sample_image(grid)
        return {
            "success": True,
            "face_grid": grid,
            "annotated_image": preview,
            "center_color": grid[1][1]
        }

    if req.image_base64:
        b64_str = req.image_base64
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        try:
            raw = base64.b64decode(b64_str)
            res = process_cube_image(raw)
            return {
                "success": True,
                "face_grid": res["face_grid"],
                "annotated_image": res["annotated_image"],
                "center_color": res["center_color"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image base64 decoding error: {str(e)}"
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing sample_id or image_base64."
    )


@router.get("/api/history")
@router.get("/api/v1/cube/history")
async def get_history(current_user: Optional[dict] = Depends(get_optional_current_user)):
    """Fetches solve history from MySQL for the authenticated user"""
    if not current_user:
        return {"history": []}
    user_history = SolveModel.get_user_history(current_user["id"], limit=50)
    # Serialize datetime fields to string
    clean_history = []
    for item in user_history:
        entry = dict(item)
        if "created_at" in entry and entry["created_at"]:
            entry["created_at"] = str(entry["created_at"])
        clean_history.append(entry)
    return {"history": clean_history}


@router.get("/api/patterns")
@router.get("/api/v1/cube/patterns")
async def get_patterns():
    """Pattern Studio library: verified artistic patterns with their move lists."""
    try:
        return {"success": True, "patterns": pattern_library.get_patterns()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
