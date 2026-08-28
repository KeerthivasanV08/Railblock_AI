"""
Custom Exception Classes and Centralized Error Handling for RailBlock AI.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class RailBlockException(Exception):
    """Base exception for RailBlock AI application."""
    def __init__(self, code: str, message: str, details: dict = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class DataFileNotFoundException(RailBlockException):
    def __init__(self, file_name: str):
        super().__init__(
            code="DATA_FILE_NOT_FOUND",
            message=f"Required data file '{file_name}' was not found.",
            details={"file": file_name},
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidCSVSchemaException(RailBlockException):
    def __init__(self, file_name: str, missing_columns: list):
        super().__init__(
            code="INVALID_CSV_SCHEMA",
            message=f"File '{file_name}' is missing required columns: {missing_columns}.",
            details={"file": file_name, "missing_columns": missing_columns},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class InvalidForeignKeyException(RailBlockException):
    def __init__(self, file_name: str, fk_col: str, orphan_count: int):
        super().__init__(
            code="INVALID_FOREIGN_KEY",
            message=f"File '{file_name}' contains {orphan_count} orphan references in '{fk_col}'.",
            details={"file": file_name, "fk_col": fk_col, "orphan_count": orphan_count},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class InfeasibleBlockException(RailBlockException):
    def __init__(self, block_id: str, rejection_reason: str):
        super().__init__(
            code="INFEASIBLE_BLOCK",
            message=f"Block '{block_id}' is operationally infeasible: {rejection_reason}.",
            details={"block_id": block_id, "rejection_reason": rejection_reason},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidApprovalActionException(RailBlockException):
    def __init__(self, action: str, reason: str):
        super().__init__(
            code="INVALID_APPROVAL_ACTION",
            message=f"Approval action '{action}' failed: {reason}.",
            details={"action": action, "reason": reason},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ResourceNotFoundException(RailBlockException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{entity} '{entity_id}' was not found.",
            details={"entity": entity, "entity_id": entity_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


async def railblock_exception_handler(request: Request, exc: RailBlockException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )
