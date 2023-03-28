from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `account` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY COMMENT '主键',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6) NOT NULL  COMMENT '更新时间',
    `username` VARCHAR(32) NOT NULL  COMMENT '用户名',
    `nickname` VARCHAR(48) NOT NULL  COMMENT '昵称',
    `phone` VARCHAR(20) NOT NULL  COMMENT '手机号',
    `password` VARCHAR(128) NOT NULL  COMMENT '密码',
    `last_login_at` DATETIME(6)   COMMENT '最近一次登录时间',
    `remark` VARCHAR(256) NOT NULL  COMMENT '备注' DEFAULT '',
    `avatar_uri` VARCHAR(256) NOT NULL  COMMENT '头像' DEFAULT '',
    `status` VARCHAR(16) NOT NULL  COMMENT '状态' DEFAULT 'enable',
    KEY `idx_account_created_028865` (`created_at`),
    KEY `idx_account_usernam_c7a6b4` (`username`),
    KEY `idx_account_phone_9b3340` (`phone`)
) CHARACTER SET utf8mb4 COMMENT='用户';
CREATE TABLE IF NOT EXISTS `permission` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY COMMENT '主键',
    `code` VARCHAR(64) NOT NULL UNIQUE COMMENT '权限码',
    `label` VARCHAR(128) NOT NULL  COMMENT '权限名称',
    `type` VARCHAR(16) NOT NULL  COMMENT '权限类型' DEFAULT 'api',
    `is_deprecated` BOOL NOT NULL  COMMENT '是否废弃' DEFAULT 0,
    KEY `idx_permission_created_0494ab` (`created_at`)
) CHARACTER SET utf8mb4 COMMENT='权限';
CREATE TABLE IF NOT EXISTS `resource` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY COMMENT '主键',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6) NOT NULL  COMMENT '更新时间',
    `code` VARCHAR(32) NOT NULL  COMMENT '资源编码{parent}:{current}',
    `label` VARCHAR(64) NOT NULL  COMMENT '资源名称',
    `front_route` VARCHAR(128)   COMMENT '前端路由',
    `type` VARCHAR(16) NOT NULL  COMMENT '组类型',
    `order_num` INT NOT NULL  DEFAULT 1,
    `启用状态` BOOL NOT NULL  COMMENT '当前分组是否可用' DEFAULT 1,
    `是否可配置` BOOL NOT NULL  COMMENT '配置时是否可分配' DEFAULT 1,
    `parent_id` CHAR(36),
    CONSTRAINT `fk_resource_resource_61c52602` FOREIGN KEY (`parent_id`) REFERENCES `resource` (`id`) ON DELETE CASCADE,
    KEY `idx_resource_created_669b66` (`created_at`),
    KEY `idx_resource_code_edb401` (`code`),
    KEY `idx_resource_label_a90213` (`label`)
) CHARACTER SET utf8mb4 COMMENT='权限';
CREATE TABLE IF NOT EXISTS `role` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY COMMENT '主键',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6) NOT NULL  COMMENT '更新时间',
    `code` VARCHAR(32) NOT NULL  COMMENT '角色编码',
    `label` VARCHAR(64) NOT NULL  COMMENT '角色名称',
    KEY `idx_role_created_7f5f71` (`created_at`),
    KEY `idx_role_code_604657` (`code`),
    KEY `idx_role_label_50ca0f` (`label`)
) CHARACTER SET utf8mb4 COMMENT='角色';
CREATE TABLE IF NOT EXISTS `system` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY COMMENT '主键',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6) NOT NULL  COMMENT '更新时间',
    `code` VARCHAR(64) NOT NULL UNIQUE COMMENT '系统唯一标识',
    `label` VARCHAR(128) NOT NULL  COMMENT '系统名称',
    KEY `idx_system_created_d577b3` (`created_at`)
) CHARACTER SET utf8mb4 COMMENT='系统';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `resource_system` (
    `resource_id` CHAR(36) NOT NULL,
    `system_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`resource_id`) REFERENCES `resource` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`system_id`) REFERENCES `system` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `resource_permission` (
    `resource_id` CHAR(36) NOT NULL,
    `permission_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`resource_id`) REFERENCES `resource` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_account` (
    `role_id` CHAR(36) NOT NULL,
    `account_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`account_id`) REFERENCES `account` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_resource` (
    `role_id` CHAR(36) NOT NULL,
    `resource_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`resource_id`) REFERENCES `resource` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_system` (
    `role_id` CHAR(36) NOT NULL,
    `system_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`system_id`) REFERENCES `system` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_permission` (
    `role_id` CHAR(36) NOT NULL,
    `permission_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
