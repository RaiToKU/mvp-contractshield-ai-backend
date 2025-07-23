# 用户ID字段修改说明

## 问题描述
线上数据库报错：`psycopg2.errors.UndefinedColumn: column "user_id" of relation "tasks" does not exist`

## 解决方案

### 1. 代码修改
- **models.py**: 修改 `Task` 模型中的 `user_id` 字段，设置为 `nullable=True, default=None`
- **file_service.py**: 修改 `save_and_enqueue` 方法，`user_id` 参数默认值改为 `None`
- **upload.py**: 移除硬编码的 `user_id=2`，暂时不传入 `user_id`

### 2. 数据库迁移
执行 `migrations/add_user_id_to_tasks.sql` 脚本：

```sql
-- 为tasks表添加user_id字段
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id INTEGER;
```

### 3. 修改后的行为
- 新创建的任务记录中，`user_id` 字段将为 `NULL`
- 为后续账号体系的实现预留了空间
- 不再硬编码用户ID，避免了数据库字段不存在的错误

### 4. 后续计划
当实现账号体系时：
1. 添加用户认证中间件
2. 从认证信息中获取真实的 `user_id`
3. 在创建任务时传入正确的 `user_id`
4. 可以考虑为 `user_id` 添加外键约束

### 5. 部署步骤
1. 先在线上数据库执行迁移脚本
2. 然后部署新的代码版本

这样修改后，系统将不再依赖硬编码的用户ID，为未来的账号体系实现提供了灵活性。