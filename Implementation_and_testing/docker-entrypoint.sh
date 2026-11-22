#!/bin/sh
set -e

# Chờ MySQL sẵn sàng
python - <<'PY'
import os, time, MySQLdb
for i in range(60):
    try:
        MySQLdb.connect(host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", 3306)),
                        user=os.environ["DB_USER"], passwd=os.environ["DB_PASSWORD"],
                        db=os.environ["DB_NAME"]).close()
        break
    except Exception as e:
        print("Đợi database...", e); time.sleep(2)
else:
    raise SystemExit("Không kết nối được database")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Chỉ nạp dữ liệu mẫu khi bật SEED_ON_START=1 (lệnh seed an toàn khi chạy lại)
if [ "$SEED_ON_START" = "0" ]; then
  python manage.py seed --force
fi

exec "$@"