# Smart Travel 椤圭洰鍏ㄩ噺璁茶В鎵嬪唽

鏇存柊鏃堕棿锛?026-03-23

杩欎唤鏂囨。鐨勭洰鏍囦笉鏄畝鍗曢噸澶?README锛岃€屾槸鎶婅繖涓」鐩寜鈥滆兘璁茬粰鑰佸笀/闈㈣瘯瀹?涓嬩竴浣嶅紑鍙戣€呭惉鈥濈殑鏂瑰紡瀹屾暣鎷嗗紑锛?

1. 杩欎釜椤圭洰鐜板湪鍒板簳鏄粈涔堛€?
2. 鍚庣銆佹暟鎹簱銆丄PI銆佸墠绔垎鍒€庝箞缁勭粐銆?
3. 鏁版嵁鏄€庝箞鏉ョ殑锛岄〉闈㈡槸鎬庝箞璺戣捣鏉ョ殑銆?
4. 褰撳墠浠ｇ爜閲屽摢浜涘湴鏂瑰凡缁忓鐢紝鍝簺鍦版柟閫傚悎涓嬩竴闃舵缁х画鍗囩骇銆?

鏈枃鍐呭鍩轰簬浠ヤ笅瀹為檯鏍告煡缁撴灉锛?

- 宸查€愪釜闃呰 `backend/` 涓?`frontend/src/` 鐨勪富瑕佹簮鐮佹枃浠躲€?
- 宸茶繛鎺ラ」鐩粯璁?MySQL 鏁版嵁搴撳苟鏍稿褰撳墠鐪熷疄琛ㄤ笌鏁版嵁閲忋€?
- 宸叉墽琛?`python manage.py check`锛岀粨鏋滈€氳繃銆?
- 宸叉墽琛?`npm run build`锛岀粨鏋滈€氳繃銆?

---

## 1. 椤圭洰涓€鍙ヨ瘽姒傛嫭

`smart_travel` 鏄竴涓洿缁曗€滀腑鍥藉煄甯?+ 鏅偣 + AI 琛岀▼ + 绀惧尯 + 鍚庡彴绠＄悊鈥濇瀯寤虹殑瀛︾敓绾у畬鏁存梾娓稿钩鍙般€?

鎶€鏈爤锛?

- 鍚庣锛欴jango 5.1 + Django REST Framework + Token Auth
- 鍓嶇锛歏ue 3 + Vue Router + Axios + Vite
- 鏁版嵁搴擄細MySQL 涓洪粯璁や富搴擄紝SQLite 浣滀负澶囩敤鍥為€€
- 鏁版嵁鏉ユ簮锛氭湰鍦?Excel + 鎼虹▼椤甸潰鐖櫕杈撳嚭鐨?Excel
- 濯掍綋鏂囦欢锛氬綋鍓嶄繚瀛樺湪鏈湴 `backend/media/`

杩欎釜椤圭洰鐨勬牳蹇冧寒鐐逛笉鏄€滄煇涓€涓鏉傜畻娉曗€濓紝鑰屾槸鎶婁竴鏉″畬鏁翠笟鍔￠摼璺仛鍑烘潵浜嗭細

- 鍩庡競涓庢櫙鐐规暟鎹噰闆?
- 鏁版嵁瀵煎叆涓庢竻娲?
- 鍚庣鎺ュ彛鍒嗗眰
- Vue 鍓嶇椤甸潰
- AI 琛岀▼瑙勫垝
- 绀惧尯浜掑姩
- 鍚庡彴绠＄悊

---

## 2. 褰撳墠瀹為檯杩愯鐘舵€?

### 2.1 褰撳墠榛樿鏁版嵁搴?

`backend/smart_travel/settings.py` 閲岄粯璁よ蛋 MySQL锛?

- host: `127.0.0.1`
- port: `3306`
- database: `smart_travel`
- user: `root`
- password: `123456`

鍚屾椂淇濈暀浜?SQLite 鍒嗘敮锛?

- 褰撶幆澧冨彉閲?`DB_ENGINE=sqlite` 鏃讹紝鏁版嵁搴撳垏鍒?`backend/db.sqlite3`

杩欒鏄庯細

1. 椤圭洰褰撳墠鐪熷疄杩愯鏁版嵁涓昏鍦?MySQL銆?
2. 浠撳簱閲岀殑 `backend/db.sqlite3` 鏇村儚涓€涓鐢ㄥ紑鍙戝叆鍙ｏ紝涓嶆槸褰撳墠涓绘暟鎹簮銆?

### 2.2 鎴嚦 2026-03-23 鐨勬湰鍦?MySQL 鏁版嵁閲?

鎴戠洿鎺ョ敤 Django ORM 鏍稿浜嗗綋鍓嶆暟鎹簱锛?

| 鏁版嵁瀵硅薄 | 鏁伴噺 |
| --- | ---: |
| 鍩庡競 `TravelCity` | 352 |
| 鏅偣 `Attraction` | 30831 |
| 甯栧瓙 `TravelPost` | 4 |
| 鐢ㄦ埛璧勬枡 `UserProfile` | 3 |
| 宸蹭繚瀛樿绋?`TravelPlan` | 7 |
| 鎿嶄綔鏃ュ織 `OperationLog` | 49 |

褰撳墠鏁版嵁搴撲腑瀛樺湪鐨勪富瑕佽〃锛?

- `core_travelcity`
- `core_attraction`
- `core_userprofile`
- `core_travelplan`
- `core_travelpost`
- `core_postlike`
- `core_postfavorite`
- `core_postcomment`
- `core_operationlog`
- `authtoken_token`
- Django 鑷甫璁よ瘉涓庤縼绉昏〃
- ????????????? `core_destination`?`core_tripplan`

### 2.3 褰撳墠宸查獙璇侀€氳繃

- `backend/.venv/Scripts/python.exe manage.py check`
- `frontend/npm run build`

璇存槑褰撳墠浠ｇ爜鑷冲皯鍦ㄢ€滈厤缃畬鏁淬€佷緷璧栭綈鍏ㄣ€佸墠鍚庣鑳芥瀯寤衡€濈殑灞傞潰鏄垚绔嬬殑銆?

---

## 3. 浠撳簱缁撴瀯鎬昏

```text
smart_travel/
鈹溾攢 backend/
鈹? 鈹溾攢 apps/
鈹? 鈹? 鈹溾攢 core/
鈹? 鈹? 鈹溾攢 users/
鈹? 鈹? 鈹溾攢 destinations/
鈹? 鈹? 鈹溾攢 planner/
鈹? 鈹? 鈹溾攢 community/
鈹? 鈹? 鈹斺攢 backoffice/
鈹? 鈹溾攢 scripts/
鈹? 鈹溾攢 media/
鈹? 鈹溾攢 smart_travel/
鈹? 鈹溾攢 manage.py
鈹? 鈹斺攢 requirements.txt
鈹溾攢 frontend/
鈹? 鈹溾攢 public/
鈹? 鈹溾攢 src/
鈹? 鈹? 鈹溾攢 components/
鈹? 鈹? 鈹溾攢 router/
鈹? 鈹? 鈹溾攢 services/
鈹? 鈹? 鈹溾攢 stores/
鈹? 鈹? 鈹溾攢 utils/
鈹? 鈹? 鈹溾攢 views/
鈹? 鈹? 鈹溾攢 App.vue
鈹? 鈹? 鈹溾攢 main.js
鈹? 鈹? 鈹斺攢 styles.css
鈹? 鈹溾攢 package.json
鈹? 鈹斺攢 vite.config.js
鈹溾攢 cities_data_excel/
鈹溾攢 crawled_city_excels/
鈹溾攢 docs/
鈹斺攢 README.md
```

鐞嗚В杩欎唤缁撴瀯鏃讹紝寤鸿鐢ㄤ竴鍙ヨ瘽璁颁綇锛?

- `backend/apps/core` 鏀锯€滄ā鍨嬪拰鍩虹璁炬柦鈥?
- 鍏朵粬 app 鏀锯€滀笟鍔￠€昏緫鈥?
- `frontend/src/views` 鏀鹃〉闈?
- `frontend/src/components` 鏀惧彲澶嶇敤缁勪欢

---

## 4. 鍚庣鏁翠綋鏋舵瀯

## 4.1 鎬诲叆鍙?

### `backend/manage.py`

鏍囧噯 Django 鍛戒护鍏ュ彛锛岃礋璐ｅ惎鍔ㄧ鐞嗗懡浠ゃ€佽縼绉汇€乺unserver銆?

### `backend/smart_travel/settings.py`

杩欐槸鍚庣鐨勬€婚厤缃枃浠讹紝鍏抽敭鐐规湁锛?

- 娉ㄥ唽 app锛歚core/users/destinations/planner/community/backoffice`
- 寮€鍚?`rest_framework` 涓?`rest_framework.authtoken`
- 榛樿鏁版嵁搴撲负 MySQL
- 鏀寔 `DB_ENGINE=sqlite`
- 寮€鍚?`CORS_ALLOW_ALL_ORIGINS = True`
- 璁よ瘉鏂瑰紡锛?
  - `TokenAuthentication`
  - `SessionAuthentication`
- 濯掍綋鐩綍锛?
  - `MEDIA_URL = /media/`
  - `MEDIA_ROOT = backend/media`

杩欎唤閰嶇疆寰堥€傚悎寮€鍙戦樁娈碉紝浣嗕笉閫傚悎鐩存帴涓婄嚎锛屽師鍥犲湪绗?11 鑺備細璁层€?

### `backend/smart_travel/urls.py`

鍏ㄥ眬璺敱鍒嗗彂锛?

- `/site-admin/` -> Django Admin
- `/api/` -> users
- `/api/` -> destinations
- `/api/` -> planner
- `/api/` -> community
- `/api/backoffice/` -> backoffice

鍙﹀鍦?`DEBUG=True` 鏃剁洿鎺ユ妸 `MEDIA_URL` 鎸傚嚭鏉ワ紝鏂逛究鏈湴棰勮涓婁紶鍥剧墖銆?

### `backend/smart_travel/asgi.py` / `wsgi.py`

鏍囧噯閮ㄧ讲鍏ュ彛锛屽綋鍓嶆病鏈夎嚜瀹氫箟閫昏緫銆?

---

## 4.2 鏁版嵁妯″瀷涓庢暟鎹簱璁捐

鎵€鏈変富妯″瀷閮介泦涓湪 `backend/apps/core/models.py`銆?

杩欐槸鏈」鐩渶閲嶈鐨勪竴浠芥枃浠讹紝鍥犱负瀹冨畾涔変簡鏁版嵁搴撶粨鏋勩€?

### 4.2.1 褰撳墠鈥滀富涓氬姟妯″瀷鈥?

| 妯″瀷 | 浣滅敤 |
| --- | --- |
| `TravelCity` | 鍩庡競/鍖哄煙/鏅尯鑱氬悎瀵硅薄 |
| `Attraction` | 鏅偣鏄庣粏 |
| `UserProfile` | 鐢ㄦ埛鎵╁睍璧勬枡 |
| `TravelPlan` | 鐢ㄦ埛淇濆瓨鐨?AI 琛岀▼ |
| `TravelPost` | 绀惧尯甯栧瓙 |
| `PostLike` | 鐐硅禐鍏崇郴 |
| `PostFavorite` | 鏀惰棌鍏崇郴 |
| `PostComment` | 璇勮涓庡洖澶?|
| `OperationLog` | 鎿嶄綔鏃ュ織 |

### 4.2.2 褰撳墠鈥滈仐鐣欐ā鍨嬧€?

| 妯″瀷 | 褰撳墠鐘舵€?|
| --- | --- |
?? `Destination` / `TripPlan` ?????? API ????????? `TravelCity` / `Attraction` / `TravelPlan` ???

