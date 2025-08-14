# risk_matrix_api.py
"""
风险矩阵 (Risk Matrix) API 模块

本模块负责处理所有与风险矩阵相关的业务逻辑与API接口。
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import pandas as pd
import io

router = APIRouter()

DEFAULT_RISK_MODEL = {
    "probability": {"极少发生": 1, "很少发生": 2, "偶尔发生": 3, "有时发生": 4, "经常发生": 5},
    "severity": {"轻微": 1, "轻度": 2, "严重": 3, "灾难": 4},
    "levels": [
        {"name": "低风险", "threshold": 4},
        {"name": "中风险", "threshold": 9},
        {"name": "高风险", "threshold": 15},
        {"name": "极高风险", "threshold": 999}
    ]
}
current_risk_model = DEFAULT_RISK_MODEL.copy()

def calculate_risk_value(prob_val: int, sev_val: int) -> int:
    return prob_val * sev_val

def determine_risk_level(risk_value: int) -> str:
    sorted_levels = sorted(current_risk_model["levels"], key=lambda x: x["threshold"])
    for level in sorted_levels:
        if risk_value <= level["threshold"]:
            return level["name"]
    return "未知风险"

class RiskAssessmentRequest(BaseModel):
    probability: str = Field(..., description="概率等级的名称，必须与当前配置中的名称完全匹配。", example="偶尔发生")
    severity: str = Field(..., description="后果等级的名称，必须与当前配置中的名称完全匹配。", example="严重")

class RiskAssessmentResponse(BaseModel):
    risk_value: int
    risk_level: str

class MatrixCell(BaseModel):
    probability: str
    severity: str
    risk_value: int
    risk_level: str

class MatrixVisualizationResponse(BaseModel):
    probability_axis: List[str]
    severity_axis: List[str]
    matrix_data: List[List[MatrixCell]]

@router.post(
    "/risk-matrix/configure",
    summary="更新风险模型配置",
    description="""
    上传一个标准的Excel(.xlsx)文件来动态更新整个风险矩阵的评估模型。
    Excel格式要求:
    - 必须是一个标准的 `.xlsx` 文件，且只包含一个工作表。
    - 第一行必须是中文表头*包含 `类型`, `名称`, `数值` 三列。
    - `类型`列的值必须是 `probability`, `severity`, 或 `level` 之一。
    """
)
async def update_risk_model_from_excel(file: UploadFile = File(...)):
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="文件格式错误，请上传一个标准的 .xlsx Excel 文件。")
    global current_risk_model
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl', header=0)
        required_columns = ['类型', '名称', '数值']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Excel文件必须包含以下中文表头: {', '.join(required_columns)}")
        new_model = {"probability": {}, "severity": {}, "levels": []}
        for _, row in df.iterrows():
            row_type = str(row['类型']).lower().strip()
            name, value = str(row['名称']), int(row['数值'])
            if row_type == 'probability': new_model['probability'][name] = value
            elif row_type == 'severity': new_model['severity'][name] = value
            elif row_type == 'level': new_model['levels'].append({"name": name, "threshold": value})
        missing_types = [key for key in ["probability", "severity", "levels"] if not new_model.get(key)]
        if missing_types:
            error_message = f"配置不完整，您的Excel文件中缺少以下类型的数据行: {', '.join(missing_types)}。请检查'类型'列是否存在拼写错误或缺少对应行。"
            raise HTTPException(status_code=400, detail=error_message)
        current_risk_model = new_model
        return {"message": "风险模型配置已成功更新。"}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"处理文件时发生未知错误: {str(e)}")

@router.get("/risk-matrix/levels", summary="获取风险评估定义")
def get_risk_levels() -> Dict[str, Any]:
    return {"probability": current_risk_model["probability"], "severity": current_risk_model["severity"]}

@router.post("/risk-matrix/assess", response_model=RiskAssessmentResponse, summary="执行单点风险评估")
def assess_risk(request: RiskAssessmentRequest):
    prob_levels = current_risk_model["probability"]
    sev_levels = current_risk_model["severity"]
    if request.probability not in prob_levels or request.severity not in sev_levels:
        raise HTTPException(status_code=400, detail="提供的概率或后果等级在当前配置中不存在。")
    prob_val = prob_levels[request.probability]
    sev_val = sev_levels[request.severity]
    risk_value = calculate_risk_value(prob_val, sev_val)
    risk_level = determine_risk_level(risk_value)
    return RiskAssessmentResponse(risk_value=risk_value, risk_level=risk_level)

@router.get("/risk-matrix/visualize", response_model=MatrixVisualizationResponse, summary="获取可视化矩阵数据")
def get_matrix_visualization():
    prob_map = current_risk_model["probability"]
    sev_map = current_risk_model["severity"]
    prob_axis = sorted(prob_map.keys(), key=prob_map.get)
    sev_axis = sorted(sev_map.keys(), key=sev_map.get)
    matrix = []
    for prob_name in prob_axis:
        row = []
        for sev_name in sev_axis:
            prob_val, sev_val = prob_map[prob_name], sev_map[sev_name]
            risk_val = calculate_risk_value(prob_val, sev_val)
            risk_lvl = determine_risk_level(risk_val)
            row.append(MatrixCell(probability=prob_name, severity=sev_name, risk_value=risk_val, risk_level=risk_lvl))
        matrix.append(row)
    return MatrixVisualizationResponse(probability_axis=prob_axis, severity_axis=sev_axis, matrix_data=matrix)