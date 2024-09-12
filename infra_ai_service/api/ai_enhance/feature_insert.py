#!/usr/bin/python3

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infra_ai_service.service.extract_spec import extract_spec_features
from infra_ai_service.service.extract_spec import process_src_rpm_from_url

router = APIRouter()


class FeatureInsertRequest(BaseModel):
    src_rpm_url: str
    os_version: str
    force_xml: bool = False


@router.post("/")
async def feature_insert(request: FeatureInsertRequest = Body(...)):
    try:
        # download and decompress .src.rpm file
        rpm_decompress_dir = process_src_rpm_from_url(
            request.src_rpm_url
        )
        feature = extract_spec_features(
            rpm_decompress_dir,
            # request.os_version,
            request.force_xml
        )

        # TODO: insert to database with interface
        # interface(os_version, feature)

        resp_data = {
            'status': 'success',
        }
        return JSONResponse(content=resp_data)
    except Exception as e:
        resp_data = {
            'status': 'error',
            'message': str(e)
        }
        return JSONResponse(content=resp_data)
