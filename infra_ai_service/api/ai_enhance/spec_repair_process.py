from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from infra_ai_service.service.spec_repair import SpecBot


router = APIRouter()


@router.post("/")
async def spec_repair_process(err_spec_file: UploadFile = File(...),
                              err_log_file: UploadFile = File(...)):
    try:
        err_spec_lines = await err_spec_file.read()
        err_log_lines = await err_log_file.read()

        err_spec_lines = err_spec_lines.decode().splitlines(keepends=True)
        err_log_lines = err_log_lines.decode().splitlines(keepends=True)

        bot = SpecBot()
        suggestion, is_repaired, repaired_spec_lines, log_content = bot.repair(
            err_spec_lines, err_log_lines)

        resp_data = {
            'suggestions': suggestion,
            'repair_status': is_repaired,
            'repair_spec': repaired_spec_lines,
            'log': log_content
        }
        return JSONResponse(content=resp_data)
    except Exception as e:
        resp_data = {
            'status': 'error',
            'message': str(e)
        }
        return JSONResponse(content=resp_data)
