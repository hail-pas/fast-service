# Validation Message template
ValidationErrorMsgTemplates = {
    "value_error.missing": "缺少必填字段",
    "value_error.any_str.max_length": "最长不超过{limit_value}个字符",
    "value_error.any_str.min_length": "至少{limit_value}个字符",
}

# 业务错误信息

# request error msg
ParameterErrorMsg = "参数错误"
JsonRequiredMsg = "请求体必须为json"
TimestampExpiredMsg = "请求已过期"
SignCheckErrorMsg = "签名校验失败"
IPNotAllowewedMsgTemplate = "IP%s不允许访问"

# response error msg
SuccessMsg = "成功"
FailedMsg = "失败"
UnauthorizedMsg = "未授权"
InternalServerErrorMsg = "服务器内部错误"
FrobiddenMsg = "禁止访问"
AuthorizationHeaderMissingMsg = "未携带授权头部信息"
AuthorizationHeaderInvalidMsg = "授权头部信息无效"
AuthorizationHeaderTypeErrorMsg = "授权头部信息类型错误"
TokenExpiredMsg = "授权已过期"

# Object 对象相关
ObjectNotExistMsgTemplate = "%s不存在"
ObjectAlreadyExistMsgTemplate = "%s已存在"
ObjectDuplicateMsgTemplate = "%s重复"
ObjectInvalidMsgTemplate = "%s无效"
ObjectNotMatchMsgTemplate = "%s不匹配"
ObjectNotSupportMsgTemplate = "%s不支持"
ObjectNotAllowMsgTemplate = "%s不允许"
ObjectNotAllowEmptyMsgTemplate = "%s不允许为空"

# Action 操作相关
ActionNotSupportMsgTemplate = "不支持的%s"
ActionNotAllowMsgTemplate = "不允许的%s"

# other
UsernameOrPasswordErrorMsg = "用户名或密码错误"
