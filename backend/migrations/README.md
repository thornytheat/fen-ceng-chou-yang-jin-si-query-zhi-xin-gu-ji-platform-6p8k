# migrations

`0001_initial.sql` 是 MySQL 8.0 的表结构基线，与 `src/models/*` 的 SQLAlchemy 定义一一对应。
容器启动时 `src/config/app.py` 先执行 `Base.metadata.create_all()`（幂等建表），
因此空库可直接起服务；本目录的 SQL 供 DBA 手工建库 / 审阅使用。

重新初始化：

```bash
docker compose exec -T db mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < migrations/0001_initial.sql
```
