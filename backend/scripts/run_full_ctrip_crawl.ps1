$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
$script = Join-Path $projectRoot "backend\scripts\crawl_ctrip_city_sights.py"
$cityUrls = Join-Path $projectRoot "backend\scripts\ctrip_city_urls_all.txt"
$outputDir = Join-Path $projectRoot "crawled_city_excels"

if (-not (Test-Path $python)) {
    throw "未找到 Python: $python"
}

if (-not (Test-Path $cityUrls)) {
    throw "未找到城市 URL 映射文件: $cityUrls"
}

& $python $script `
    --city-urls-file $cityUrls `
    --output-dir $outputDir `
    --skip-existing `
    --delay 0.1 `
    --max-pages 3 `
    --max-attractions 30
