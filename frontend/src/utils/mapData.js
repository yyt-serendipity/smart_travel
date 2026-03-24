const PROVINCE_LAYOUT = {
  新疆维吾尔自治区: { x: 4, y: 3, shortName: "新疆" },
  西藏自治区: { x: 5, y: 8, shortName: "西藏" },
  青海省: { x: 7, y: 6, shortName: "青海" },
  甘肃省: { x: 9, y: 5, shortName: "甘肃" },
  宁夏回族自治区: { x: 11, y: 5, shortName: "宁夏" },
  内蒙古自治区: { x: 12, y: 2, shortName: "内蒙古" },
  黑龙江省: { x: 20, y: 1, shortName: "黑龙江" },
  吉林省: { x: 19, y: 3, shortName: "吉林" },
  辽宁省: { x: 18, y: 5, shortName: "辽宁" },
  河北省: { x: 16, y: 7, shortName: "河北" },
  北京市: { x: 17, y: 6, shortName: "北京" },
  天津市: { x: 18, y: 6, shortName: "天津" },
  山西省: { x: 14, y: 7, shortName: "山西" },
  陕西省: { x: 12, y: 8, shortName: "陕西" },
  河南省: { x: 15, y: 9, shortName: "河南" },
  山东省: { x: 18, y: 8, shortName: "山东" },
  江苏省: { x: 19, y: 10, shortName: "江苏" },
  上海市: { x: 20, y: 11, shortName: "上海" },
  安徽省: { x: 17, y: 10, shortName: "安徽" },
  湖北省: { x: 14, y: 11, shortName: "湖北" },
  重庆市: { x: 11, y: 11, shortName: "重庆" },
  四川省: { x: 9, y: 11, shortName: "四川" },
  贵州省: { x: 11, y: 13, shortName: "贵州" },
  云南省: { x: 8, y: 14, shortName: "云南" },
  广西壮族自治区: { x: 13, y: 15, shortName: "广西" },
  湖南省: { x: 14, y: 13, shortName: "湖南" },
  江西省: { x: 17, y: 13, shortName: "江西" },
  浙江省: { x: 20, y: 12, shortName: "浙江" },
  福建省: { x: 19, y: 14, shortName: "福建" },
  广东省: { x: 17, y: 15, shortName: "广东" },
  海南省: { x: 16, y: 18, shortName: "海南" },
  香港特别行政区: { x: 18, y: 16, shortName: "香港" },
  澳门特别行政区: { x: 17, y: 16, shortName: "澳门" },
  台湾省: { x: 21, y: 15, shortName: "台湾" },
};

const FALLBACK_LAYOUT = [
  { x: 22, y: 3 },
  { x: 22, y: 5 },
  { x: 22, y: 7 },
  { x: 22, y: 9 },
  { x: 22, y: 11 },
  { x: 22, y: 13 },
  { x: 22, y: 15 },
];

function normalizeProvinceName(value) {
  return value?.trim() || "未分省";
}

export function shortProvinceName(value) {
  const province = normalizeProvinceName(value);
  return PROVINCE_LAYOUT[province]?.shortName || province.replace(/省|市|壮族自治区|回族自治区|维吾尔自治区|自治区|特别行政区/g, "");
}

export function buildProvinceStats(cities = []) {
  const grouped = new Map();

  cities.forEach((city) => {
    const province = normalizeProvinceName(city.province);
    if (!grouped.has(province)) {
      grouped.set(province, {
        province,
        shortName: shortProvinceName(province),
        cityCount: 0,
        attractionCount: 0,
        averageRating: 0,
        topCity: null,
        cities: [],
      });
    }
    const item = grouped.get(province);
    item.cityCount += 1;
    item.attractionCount += city.attraction_count || 0;
    item.averageRating += Number(city.average_rating || 0);
    item.cities.push(city);
    if (!item.topCity || (city.attraction_count || 0) > (item.topCity.attraction_count || 0)) {
      item.topCity = city;
    }
  });

  return [...grouped.values()]
    .map((item, index) => {
      const meta = PROVINCE_LAYOUT[item.province] || FALLBACK_LAYOUT[index % FALLBACK_LAYOUT.length];
      return {
        ...item,
        x: meta.x,
        y: meta.y,
        shortName: meta.shortName || item.shortName,
        averageRating: item.cityCount ? Number((item.averageRating / item.cityCount).toFixed(1)) : 0,
      };
    })
    .sort((a, b) => b.attractionCount - a.attractionCount);
}

export function dedupeTags(items = []) {
  const tagSet = new Set();
  items.forEach((item) => {
    (item.tags || []).forEach((tag) => tagSet.add(tag));
  });
  return [...tagSet];
}

export function normalizeProvince(value) {
  return normalizeProvinceName(value);
}
