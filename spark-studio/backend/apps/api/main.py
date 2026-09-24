"""
Spark Studio Backend — 提供 3DGS 文件服务和格式转换 API

运行:
    uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8004
"""

from __future__ import annotations

import os
import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

app = FastAPI(
    title="Spark Studio API",
    description="3D Gaussian Splatting 可视化后端服务",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("SPARK_CORS_ORIGIN", "http://localhost:5174"),
        "http://localhost:8003",  # 主前端
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录（可配置）
DATA_DIR = Path(os.getenv("SPARK_DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 支持的格式
SUPPORTED_EXTENSIONS = {".spz", ".ply", ".splat", ".ksplat", ".sog", ".rad"}


# ─── 数据模型 ─────────────────────────────────────────────


class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    format: str


class FileListResponse(BaseModel):
    files: list[FileInfo]
    total: int


# ─── 辅助函数 ─────────────────────────────────────────────


def _is_supported(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def _get_file_list() -> list[FileInfo]:
    """扫描数据目录，列出所有支持的 3DGS 文件"""
    files: list[FileInfo] = []
    if not DATA_DIR.exists():
        return files

    for f in sorted(DATA_DIR.iterdir()):
        if f.is_file() and _is_supported(f):
            files.append(
                FileInfo(
                    name=f.name,
                    path=f"/api/files/{f.name}",
                    size=f.stat().st_size,
                    format=f.suffix.lower(),
                )
            )
    return files


# ─── API 路由 ─────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "spark-studio"}


@app.get("/api/files", response_model=FileListResponse)
async def list_files():
    """列出所有可用的 3DGS 文件"""
    files = _get_file_list()
    return FileListResponse(files=files, total=len(files))


@app.get("/api/files/{filename:path}")
async def get_file(filename: str, request: Request):
    """
    获取 3DGS 文件（支持 HTTP Range 请求，用于 .rad 流式加载）

    SPARK 2.0 的 .rad 格式依赖 HTTP Range 请求实现渐进式加载，
    因此必须正确处理 Range header。
    """
    file_path = DATA_DIR / filename

    # 安全检查：防止目录遍历
    try:
        file_path = file_path.resolve()
        DATA_DIR.resolve()
        if not str(file_path).startswith(str(DATA_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Forbidden")
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    file_size = file_path.stat().st_size

    # 猜测 MIME 类型
    media_type, _ = mimetypes.guess_type(str(file_path))
    if not media_type:
        media_type = "application/octet-stream"

    # 处理 Range 请求（流式加载关键）
    range_header = request.headers.get("range")
    if range_header:
        start, end = 0, file_size - 1
        try:
            range_match = range_header.replace("bytes=", "").split("-")
            start = int(range_match[0])
            if range_match[1]:
                end = int(range_match[1])
        except (ValueError, IndexError):
            pass

        if start >= file_size or end >= file_size:
            return Response(status_code=416)

        # 读取文件块
        with open(file_path, "rb") as f:
            f.seek(start)
            chunk_size = end - start + 1
            body = f.read(chunk_size)

        return Response(
            content=body,
            status_code=206,
            media_type=media_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(len(body)),
                "Accept-Ranges": "bytes",
            },
        )

    # 非 Range 请求：返回完整文件
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        },
    )


@app.post("/api/upload")
async def upload_file(file: bytes, filename: str = ""):
    """
    上传 3DGS 文件到数据目录
    """
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    dest = DATA_DIR / filename
    with open(dest, "wb") as f:
        f.write(file)

    return JSONResponse(
        content={
            "message": "Upload successful",
            "file": {
                "name": filename,
                "path": f"/api/files/{filename}",
                "size": dest.stat().st_size,
            },
        },
        status_code=201,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.api.main:app", host="127.0.0.1", port=8004, reload=True)
