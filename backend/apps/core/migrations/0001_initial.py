from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Destination",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="目的地名称")),
                ("city", models.CharField(max_length=100, verbose_name="城市")),
                ("country", models.CharField(max_length=100, verbose_name="国家/地区")),
                ("tagline", models.CharField(max_length=180, verbose_name="短标语")),
                ("description", models.TextField(verbose_name="目的地介绍")),
                ("cover_gradient", models.CharField(blank=True, max_length=120, verbose_name="封面渐变")),
                ("best_season", models.CharField(max_length=100, verbose_name="推荐季节")),
                ("trip_days_min", models.PositiveIntegerField(default=3, verbose_name="最短游玩天数")),
                ("trip_days_max", models.PositiveIntegerField(default=8, verbose_name="最长游玩天数")),
                ("estimated_budget", models.PositiveIntegerField(default=6000, verbose_name="人均预算")),
                ("rating", models.DecimalField(decimal_places=1, default=4.8, max_digits=3, verbose_name="推荐指数")),
                ("tags", models.JSONField(blank=True, default=list, verbose_name="标签")),
                ("highlights", models.JSONField(blank=True, default=list, verbose_name="亮点")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-rating", "name"]},
        ),
        migrations.CreateModel(
            name="TripPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="行程标题")),
                ("traveler_name", models.CharField(max_length=100, verbose_name="出行人")),
                ("departure_city", models.CharField(max_length=100, verbose_name="出发城市")),
                ("destination_name", models.CharField(max_length=100, verbose_name="主目的地")),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="出发日期")),
                ("duration_days", models.PositiveIntegerField(default=5, verbose_name="出行天数")),
                ("travel_style", models.CharField(max_length=100, verbose_name="旅行风格")),
                ("budget_level", models.CharField(default="balanced", max_length=50, verbose_name="预算档位")),
                ("companions", models.CharField(default="双人", max_length=60, verbose_name="同行方式")),
                ("interests", models.JSONField(blank=True, default=list, verbose_name="兴趣偏好")),
                ("summary", models.TextField(blank=True, verbose_name="方案摘要")),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "待确认"), ("active", "进行中"), ("completed", "已完成")],
                        default="draft",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("total_budget", models.PositiveIntegerField(default=0, verbose_name="预算估算")),
                ("daily_outline", models.JSONField(blank=True, default=list, verbose_name="日程概览")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
