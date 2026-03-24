from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

from apps.community.models import TravelPost
from apps.core.tagging import normalize_profile_styles
from apps.destinations.models import TravelCity
from apps.destinations.importers import import_excel_directory
from apps.destinations.services import default_excel_directory
from apps.users.services import ensure_user_profile


User = get_user_model()


class Command(BaseCommand):
    help = "初始化演示账号、城市数据和社区示例帖子。"

    def handle(self, *args, **options):
        excel_dir = default_excel_directory()
        if Path(excel_dir).exists() and TravelCity.objects.count() == 0:
            imported = import_excel_directory(excel_dir, overwrite=False, limit=40)
            self.stdout.write(self.style.SUCCESS(f"已从 Excel 导入 {len(imported)} 个城市工作簿。"))

        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password("admin123456")
            admin_user.save()
        ensure_user_profile(admin_user)
        admin_token, _ = Token.objects.get_or_create(user=admin_user)

        traveler_user, created = User.objects.get_or_create(username="traveler")
        if created:
            traveler_user.set_password("travel123456")
            traveler_user.save()
        profile = ensure_user_profile(traveler_user)
        if not profile.nickname:
            profile.nickname = "漫游旅人"
            profile.home_city = "成都"
            profile.favorite_styles = normalize_profile_styles(["自然风光", "摄影"])
            profile.save()
        traveler_token, _ = Token.objects.get_or_create(user=traveler_user)

        cities = list(TravelCity.objects.order_by("-average_rating")[:3])
        post_templates = [
            ("第一次去九寨沟怎么安排更顺", "建议把核心景点拆成高海拔观景段和轻松漫游段，不要一天塞太满。"),
            ("北京三天两晚城市漫游攻略", "故宫、景山、什刹海和胡同片区可以串成一条很舒服的路线。"),
            ("成都适合慢慢逛的几条线", "如果你喜欢城市烟火感，可以把宽窄巷子、望平街和东郊记忆拆开玩。"),
        ]

        for city, template in zip(cities, post_templates):
            TravelPost.objects.get_or_create(
                author=traveler_user,
                city=city,
                title=template[0],
                defaults={
                    "content": template[1],
                    "cover_image": city.cover_image,
                    "tags": city.tags[:3],
                    "status": TravelPost.STATUS_PUBLISHED,
                },
            )

        self.stdout.write(self.style.SUCCESS("演示数据初始化完成。"))
        self.stdout.write(self.style.SUCCESS(f"Admin token: {admin_token.key}"))
        self.stdout.write(self.style.SUCCESS(f"Traveler token: {traveler_token.key}"))
