# -*- coding: utf-8 -*-

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.core.base_schema import BaseSchema
from app.core.validator import role_permission_request_validator
from app.core.validator import DateTimeStr
from ..menu.schema import MenuOutSchema


class RoleCreateSchema(BaseModel):
    """角色创建模型"""
    name: str = Field(..., max_length=40, description="角色名称")
    code: Optional[str] = Field(default=None, max_length=40, description="角色编码")
    order: Optional[int] = Field(default=1, ge=1, description='显示排序')
    data_scope: Optional[int] = Field(default=1, ge=1, le=5, description='数据权限范围')
    status: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(default=None, max_length=255, description="描述")

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: Optional[str]):
        if value is None:
            return value
        import re
        v = value.strip()
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]{1,39}$", v):
            raise ValueError("角色编码需字母开头，允许字母/数字/下划线，长度2-40")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        v = value.strip()
        if not v:
            raise ValueError("角色名称不能为空")
        return v

    @model_validator(mode='before')
    @classmethod
    def _normalize(cls, values):
        if isinstance(values, dict):
            for k in ["name", "code", "description"]:
                if k in values and isinstance(values[k], str):
                    values[k] = values[k].strip() or None if values[k].strip() == "" else values[k].strip()
            # bool 兼容
            if "status" in values and isinstance(values["status"], str):
                values["status"] = values["status"].strip().lower() in {"true", "1", "yes", "y"}
            # 数字兼容
            if "order" in values and isinstance(values["order"], str):
                try:
                    values["order"] = int(values["order"].strip())
                except Exception:
                    pass
        return values

    @model_validator(mode='after')
    def _validate_after(self):
        if self.status is False and (not self.description or not str(self.description).strip()):
            raise ValueError("禁用状态下必须填写描述")
        return self


class RolePermissionSettingSchema(BaseModel):
    """角色权限配置模型"""
    data_scope: int = Field(default=1, ge=1, le=5, description='数据权限范围')
    role_ids: List[int] = Field(default_factory=list, description='角色ID列表')
    menu_ids: List[int] = Field(default_factory=list, description='菜单ID列表')
    # dept_ids removed
    
    @model_validator(mode='before')
    @classmethod
    def _normalize(cls, values):
        if isinstance(values, dict):
            for k in ["role_ids", "menu_ids"]:
                if k in values and values[k] is not None:
                    try:
                        values[k] = list({int(x) for x in values[k]})
                    except Exception:
                        pass
        return values
    
    @model_validator(mode='after')
    def validate_fields(self):
        """验证权限配置字段"""
        return role_permission_request_validator(self)


class RoleUpdateSchema(RoleCreateSchema):
    """角色更新模型"""
    ...


class RoleOutSchema(RoleCreateSchema, BaseSchema):
    """角色信息响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    menus: List[MenuOutSchema] = Field(default_factory=list, description='角色菜单列表')
    # depts removed


class RoleOptionsOut(RoleCreateSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="主键ID")
    created_at: DateTimeStr = Field(..., description="创建时间")
    updated_at: DateTimeStr = Field(..., description="更新时间")
    menus: List[MenuOutSchema] = Field(default_factory=list, description='角色菜单列表')