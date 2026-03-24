from django.db import models


# Keep the historical `core` app label so existing tables and migrations remain valid
# while model code lives in the domain app.
CORE_APP_LABEL = "core"


class Destination(models.Model):
    name = models.CharField("目的地名称", max_length=100, unique=True)
    city = models.CharField("城市", max_length=100)
    country = models.CharField("国家/地区", max_length=100)
    tagline = models.CharField("短标语", max_length=180)
    description = models.TextField("目的地介绍")
    cover_gradient = models.CharField("封面渐变", max_length=120, blank=True)
    best_season = models.CharField("推荐季节", max_length=100)
    trip_days_min = models.PositiveIntegerField("最短游玩天数", default=3)
    trip_days_max = models.PositiveIntegerField("最长游玩天数", default=8)
    estimated_budget = models.PositiveIntegerField("人均预算", default=6000)
    rating = models.DecimalField("推荐指数", max_digits=3, decimal_places=1, default=4.8)
    tags = models.JSONField("标签", default=list, blank=True)
    highlights = models.JSONField("亮点", default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["-rating", "name"]

    def __str__(self) -> str:
        return self.name


class TravelCity(models.Model):
    DESTINATION_TYPE_CHOICES = [
        ("city", "城市"),
        ("region", "区域"),
        ("scenic", "景区"),
    ]

    name = models.CharField("目的地名称", max_length=100, unique=True)
    province = models.CharField("省份/直辖市", max_length=100, blank=True)
    destination_type = models.CharField("目的地类型", max_length=20, choices=DESTINATION_TYPE_CHOICES, default="city")
    short_intro = models.CharField("短介绍", max_length=220, blank=True)
    overview = models.TextField("概述", blank=True)
    travel_highlights = models.TextField("玩法亮点", blank=True)
    cover_image = models.URLField("封面图", blank=True, max_length=500)
    best_season = models.CharField("推荐季节", max_length=200, blank=True)
    recommended_days = models.PositiveIntegerField("建议游玩天数", default=2)
    average_rating = models.DecimalField("平均评分", max_digits=3, decimal_places=1, null=True, blank=True)
    average_ticket = models.CharField("门票参考", max_length=255, blank=True)
    attraction_count = models.PositiveIntegerField("景点数量", default=0)
    tags = models.JSONField("标签", default=list, blank=True)
    travel_tips = models.TextField("出行建议", blank=True)
    source_file = models.CharField("来源文件", max_length=255, blank=True)
    is_featured = models.BooleanField("首页推荐", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["-is_featured", "-average_rating", "name"]

    def __str__(self) -> str:
        return self.name


class Attraction(models.Model):
    city = models.ForeignKey(TravelCity, related_name="attractions", on_delete=models.CASCADE)
    name = models.CharField("景点名称", max_length=200)
    source_url = models.URLField("来源链接", blank=True)
    address = models.TextField("地址", blank=True)
    description = models.TextField("介绍", blank=True)
    opening_hours = models.TextField("开放时间", blank=True)
    image_url = models.URLField("图片链接", blank=True, max_length=500)
    rating = models.DecimalField("评分", max_digits=3, decimal_places=1, null=True, blank=True)
    suggested_play_time = models.CharField("建议游玩时间", max_length=120, blank=True)
    best_season = models.CharField("建议季节", max_length=255, blank=True)
    ticket_info = models.TextField("门票", blank=True)
    tips = models.TextField("小贴士", blank=True)
    source_page = models.PositiveIntegerField("来源页码", default=1)
    tags = models.JSONField("景点标签", default=list, blank=True)
    source_file = models.CharField("来源文件", max_length=255, blank=True)
    imported_from_excel = models.BooleanField("来自 Excel", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = CORE_APP_LABEL
        ordering = ["-rating", "name"]
        constraints = [
            models.UniqueConstraint(fields=["city", "name"], name="uniq_attraction_city_name"),
        ]

    def __str__(self) -> str:
        return f"{self.city.name} - {self.name}"
